"""
Content Moderator

This module implements the core moderation engine that converts model predictions
into actionable moderation decisions.
"""

import logging
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, asdict
import json

from .rules import ModerationRules, ModerationAction, SeverityLevel, PresetRules

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class ModerationResult:
    """
    Result of content moderation analysis.
    
    Attributes
    ----------
    action : str
        Recommended moderation action (ALLOW, WARNING, HIDE, BLOCK)
    severity : str
        Severity level (NONE, LOW, MEDIUM, HIGH, CRITICAL)
    primary_label : str
        Primary toxic category detected
    confidence : float
        Confidence score for the decision (0.0 to 1.0)
    all_predictions : Dict[str, float]
        All toxicity predictions from the model
    explanation : str
        Human-readable explanation of the decision
    metadata : Dict
        Additional metadata (thresholds used, flags, etc.)
    """
    action: str
    severity: str
    primary_label: str
    confidence: float
    all_predictions: Dict[str, float]
    explanation: str
    metadata: Dict
    
    def to_dict(self) -> Dict:
        """Convert result to dictionary."""
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        """Convert result to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    def is_safe(self) -> bool:
        """Check if content is safe (ALLOW action)."""
        return self.action == ModerationAction.ALLOW.value
    
    def requires_action(self) -> bool:
        """Check if content requires moderation action."""
        return self.action in [
            ModerationAction.HIDE.value,
            ModerationAction.BLOCK.value
        ]
    
    def is_critical(self) -> bool:
        """Check if content is critically toxic."""
        return self.severity == SeverityLevel.CRITICAL.value


class ContentModerator:
    """
    Production-ready content moderation engine.
    
    This class converts toxicity model predictions into actionable moderation
    decisions using configurable rules and thresholds.
    
    Parameters
    ----------
    rules : ModerationRules, optional
        Moderation rules configuration. If None, uses default moderate rules.
    
    Examples
    --------
    >>> moderator = ContentModerator()
    >>> predictions = {'toxic': 0.85, 'insult': 0.72, 'obscene': 0.45}
    >>> result = moderator.moderate(predictions)
    >>> print(result.action)  # "BLOCK"
    >>> print(result.severity)  # "HIGH"
    """
    
    def __init__(self, rules: Optional[ModerationRules] = None):
        """
        Initialize content moderator.
        
        Parameters
        ----------
        rules : ModerationRules, optional
            Moderation rules. If None, uses default moderate rules.
        """
        self.rules = rules if rules is not None else ModerationRules()
        logger.info(f"Initialized ContentModerator with {self.rules.aggregation_strategy} aggregation")
    
    def moderate(
        self,
        predictions: Dict[str, float],
        text: Optional[str] = None,
        user_id: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> ModerationResult:
        """
        Perform moderation analysis on content.
        
        Parameters
        ----------
        predictions : Dict[str, float]
            Model predictions: {label: score}
            Example: {'toxic': 0.85, 'insult': 0.72, 'obscene': 0.45}
        text : str, optional
            Original text content (for logging/auditing)
        user_id : str, optional
            User identifier (for logging/auditing)
        context : Dict, optional
            Additional context (platform, channel, etc.)
        
        Returns
        -------
        ModerationResult
            Comprehensive moderation decision
        
        Raises
        ------
        ValueError
            If predictions are invalid or empty
        """
        # Validate input
        if not predictions:
            raise ValueError("Predictions dictionary cannot be empty")
        
        if not all(0.0 <= score <= 1.0 for score in predictions.values()):
            raise ValueError("All prediction scores must be between 0.0 and 1.0")
        
        try:
            # Step 1: Aggregate multi-label predictions
            aggregated_score, primary_label = self.rules.aggregate_scores(predictions)
            
            # Step 2: Check for critical labels
            is_critical = any(
                self.rules.is_critical_label(label, score)
                for label, score in predictions.items()
            )
            
            # Step 3: Determine moderation action
            action = self.rules.get_action_for_score(aggregated_score)
            
            # Step 4: Determine severity level
            severity = self.rules.get_severity_for_score(aggregated_score)
            
            # Override severity if critical label detected
            if is_critical:
                severity = SeverityLevel.CRITICAL
                # Escalate action if needed
                if action == ModerationAction.ALLOW:
                    action = ModerationAction.WARNING
                elif action == ModerationAction.WARNING:
                    action = ModerationAction.HIDE
            
            # Step 5: Generate explanation
            explanation = self._generate_explanation(
                action=action,
                severity=severity,
                primary_label=primary_label,
                confidence=aggregated_score,
                predictions=predictions,
                is_critical=is_critical
            )
            
            # Step 6: Compile metadata
            metadata = {
                'aggregated_score': round(aggregated_score, 4),
                'aggregation_strategy': self.rules.aggregation_strategy,
                'is_critical_label': is_critical,
                'num_labels_detected': sum(1 for s in predictions.values() if s >= self.rules.min_confidence),
                'thresholds_used': {
                    'action': self.rules.thresholds[action],
                    'severity': self.rules.severity_thresholds[severity]
                }
            }
            
            # Add optional context
            if user_id:
                metadata['user_id'] = user_id
            if context:
                metadata['context'] = context
            if text:
                metadata['text_length'] = len(text)
            
            # Step 7: Create result
            result = ModerationResult(
                action=action.value,
                severity=severity.value,
                primary_label=primary_label,
                confidence=round(aggregated_score, 4),
                all_predictions={k: round(v, 4) for k, v in predictions.items()},
                explanation=explanation,
                metadata=metadata
            )
            
            # Log decision
            logger.info(
                f"Moderation decision: {action.value} | "
                f"Severity: {severity.value} | "
                f"Primary: {primary_label} | "
                f"Confidence: {aggregated_score:.4f}"
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Error during moderation: {str(e)}", exc_info=True)
            raise
    
    def moderate_batch(
        self,
        predictions_list: List[Dict[str, float]],
        texts: Optional[List[str]] = None,
        user_ids: Optional[List[str]] = None
    ) -> List[ModerationResult]:
        """
        Perform moderation on multiple contents.
        
        Parameters
        ----------
        predictions_list : List[Dict[str, float]]
            List of prediction dictionaries
        texts : List[str], optional
            List of original texts
        user_ids : List[str], optional
            List of user identifiers
        
        Returns
        -------
        List[ModerationResult]
            List of moderation results
        """
        results = []
        
        for i, predictions in enumerate(predictions_list):
            text = texts[i] if texts and i < len(texts) else None
            user_id = user_ids[i] if user_ids and i < len(user_ids) else None
            
            try:
                result = self.moderate(
                    predictions=predictions,
                    text=text,
                    user_id=user_id
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Error moderating item {i}: {str(e)}")
                # Create error result
                results.append(self._create_error_result(predictions, str(e)))
        
        return results
    
    def _generate_explanation(
        self,
        action: ModerationAction,
        severity: SeverityLevel,
        primary_label: str,
        confidence: float,
        predictions: Dict[str, float],
        is_critical: bool
    ) -> str:
        """
        Generate human-readable explanation for moderation decision.
        
        Parameters
        ----------
        action : ModerationAction
            Moderation action taken
        severity : SeverityLevel
            Severity level
        primary_label : str
            Primary toxic category
        confidence : float
            Confidence score
        predictions : Dict[str, float]
            All predictions
        is_critical : bool
            Whether critical label was detected
        
        Returns
        -------
        str
            Human-readable explanation
        """
        # Get all significant labels
        significant_labels = [
            label for label, score in predictions.items()
            if score >= self.rules.min_confidence
        ]
        
        # Build explanation
        if action == ModerationAction.ALLOW:
            if not significant_labels:
                return "Content appears safe with no significant toxicity detected."
            else:
                return (
                    f"Content shows minimal toxicity ({primary_label}: {confidence:.2f}). "
                    f"Below threshold for action."
                )
        
        elif action == ModerationAction.WARNING:
            return (
                f"Content contains {severity.value.lower()} toxicity "
                f"(primary: {primary_label}, confidence: {confidence:.2f}). "
                f"Consider showing a warning or flagging for review."
            )
        
        elif action == ModerationAction.HIDE:
            if is_critical:
                return (
                    f"Content contains critical toxicity ({primary_label}) "
                    f"and should be hidden from public view. "
                    f"Detected: {', '.join(significant_labels)}."
                )
            else:
                return (
                    f"Content contains {severity.value.lower()} toxicity "
                    f"(primary: {primary_label}, confidence: {confidence:.2f}). "
                    f"Recommended to hide from public view."
                )
        
        elif action == ModerationAction.BLOCK:
            if is_critical:
                return (
                    f"Content contains severe violations ({primary_label}) "
                    f"and must be blocked immediately. "
                    f"Critical categories detected: {', '.join(significant_labels)}."
                )
            else:
                return (
                    f"Content contains severe toxicity "
                    f"(primary: {primary_label}, confidence: {confidence:.2f}). "
                    f"Recommended to block and remove content."
                )
        
        return "Unable to generate explanation."
    
    def _create_error_result(
        self,
        predictions: Dict[str, float],
        error_message: str
    ) -> ModerationResult:
        """
        Create error result when moderation fails.
        
        Parameters
        ----------
        predictions : Dict[str, float]
            Original predictions
        error_message : str
            Error message
        
        Returns
        -------
        ModerationResult
            Error result with WARNING action
        """
        return ModerationResult(
            action=ModerationAction.WARNING.value,
            severity=SeverityLevel.MEDIUM.value,
            primary_label="error",
            confidence=0.0,
            all_predictions=predictions,
            explanation=f"Moderation error: {error_message}. Defaulting to WARNING.",
            metadata={'error': error_message}
        )
    
    def get_statistics(
        self,
        results: List[ModerationResult]
    ) -> Dict:
        """
        Calculate statistics from moderation results.
        
        Parameters
        ----------
        results : List[ModerationResult]
            List of moderation results
        
        Returns
        -------
        dict
            Statistics summary
        """
        if not results:
            return {}
        
        total = len(results)
        
        # Count actions
        action_counts = {}
        for action in ModerationAction:
            count = sum(1 for r in results if r.action == action.value)
            action_counts[action.value] = {
                'count': count,
                'percentage': round(count / total * 100, 2)
            }
        
        # Count severities
        severity_counts = {}
        for severity in SeverityLevel:
            count = sum(1 for r in results if r.severity == severity.value)
            severity_counts[severity.value] = {
                'count': count,
                'percentage': round(count / total * 100, 2)
            }
        
        # Primary labels
        label_counts = {}
        for result in results:
            label = result.primary_label
            label_counts[label] = label_counts.get(label, 0) + 1
        
        # Average confidence
        avg_confidence = sum(r.confidence for r in results) / total
        
        return {
            'total_moderated': total,
            'actions': action_counts,
            'severities': severity_counts,
            'primary_labels': label_counts,
            'average_confidence': round(avg_confidence, 4),
            'requires_action_count': sum(1 for r in results if r.requires_action()),
            'critical_count': sum(1 for r in results if r.is_critical())
        }
    
    def update_rules(self, rules: ModerationRules):
        """
        Update moderation rules.
        
        Parameters
        ----------
        rules : ModerationRules
            New rules configuration
        """
        self.rules = rules
        logger.info("Moderation rules updated")
    
    def export_config(self) -> Dict:
        """
        Export current configuration.
        
        Returns
        -------
        dict
            Configuration dictionary
        """
        return self.rules.to_dict()
    
    @classmethod
    def from_preset(cls, preset: str) -> 'ContentModerator':
        """
        Create moderator from preset configuration.
        
        Parameters
        ----------
        preset : str
            Preset name: 'strict', 'moderate', 'lenient', 'zero_tolerance'
        
        Returns
        -------
        ContentModerator
            Configured moderator instance
        
        Raises
        ------
        ValueError
            If preset name is invalid
        """
        preset_map = {
            'strict': PresetRules.strict,
            'moderate': PresetRules.moderate,
            'lenient': PresetRules.lenient,
            'zero_tolerance': PresetRules.zero_tolerance
        }
        
        if preset not in preset_map:
            raise ValueError(
                f"Invalid preset: {preset}. "
                f"Choose from: {', '.join(preset_map.keys())}"
            )
        
        rules = preset_map[preset]()
        logger.info(f"Created ContentModerator with '{preset}' preset")
        return cls(rules=rules)
