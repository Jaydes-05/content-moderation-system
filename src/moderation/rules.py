"""
Moderation Rules and Configuration

This module defines the rules, thresholds, and configurations for content moderation.
It provides a centralized, configurable system for moderation decisions.
"""

from enum import Enum
from typing import Dict, List, Tuple
from dataclasses import dataclass, field


class ModerationAction(Enum):
    """
    Moderation actions that can be taken on content.
    
    ALLOW: Content is safe, no action needed
    WARNING: Content may be problematic, flag for review or show warning
    HIDE: Content should be hidden from public view, visible only to author
    BLOCK: Content should be completely blocked and removed
    """
    ALLOW = "ALLOW"
    WARNING = "WARNING"
    HIDE = "HIDE"
    BLOCK = "BLOCK"


class SeverityLevel(Enum):
    """
    Severity levels for toxic content.
    
    NONE: No toxicity detected
    LOW: Mild toxicity, may be acceptable in some contexts
    MEDIUM: Moderate toxicity, requires attention
    HIGH: Severe toxicity, immediate action required
    CRITICAL: Extreme toxicity (threats, hate speech), urgent action required
    """
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class ModerationRules:
    """
    Configurable moderation rules and thresholds.
    
    This class centralizes all moderation configuration, making it easy to
    adjust thresholds and rules without modifying core logic.
    
    Attributes
    ----------
    thresholds : Dict[ModerationAction, Tuple[float, float]]
        Score ranges for each moderation action (min, max)
    severity_thresholds : Dict[SeverityLevel, float]
        Minimum scores for each severity level
    label_weights : Dict[str, float]
        Importance weights for each toxicity label (higher = more severe)
    critical_labels : List[str]
        Labels that trigger critical severity regardless of score
    min_confidence : float
        Minimum confidence score to trust predictions
    """
    
    # Moderation action thresholds (score ranges)
    thresholds: Dict[ModerationAction, Tuple[float, float]] = field(default_factory=lambda: {
        ModerationAction.ALLOW: (0.0, 0.3),
        ModerationAction.WARNING: (0.3, 0.6),
        ModerationAction.HIDE: (0.6, 0.8),
        ModerationAction.BLOCK: (0.8, 1.0)
    })
    
    # Severity level thresholds (minimum scores)
    severity_thresholds: Dict[SeverityLevel, float] = field(default_factory=lambda: {
        SeverityLevel.NONE: 0.0,
        SeverityLevel.LOW: 0.3,
        SeverityLevel.MEDIUM: 0.5,
        SeverityLevel.HIGH: 0.7,
        SeverityLevel.CRITICAL: 0.85
    })
    
    # Label importance weights (higher = more severe)
    label_weights: Dict[str, float] = field(default_factory=lambda: {
        'threat': 1.5,           # Threats are most severe
        'severe_toxic': 1.4,     # Severe toxicity is very serious
        'identity_hate': 1.3,    # Hate speech is critical
        'insult': 1.0,           # Insults are moderately severe
        'obscene': 0.9,          # Obscenity is less severe
        'toxic': 0.8             # General toxicity is baseline
    })
    
    # Labels that always trigger critical severity (if score > 0.7)
    critical_labels: List[str] = field(default_factory=lambda: [
        'threat',
        'severe_toxic',
        'identity_hate'
    ])
    
    # Minimum confidence to trust predictions
    min_confidence: float = 0.5
    
    # Multi-label aggregation strategy
    aggregation_strategy: str = "weighted_max"  # Options: "max", "weighted_max", "average"
    
    def get_action_for_score(self, score: float) -> ModerationAction:
        """
        Determine moderation action based on score.
        
        Parameters
        ----------
        score : float
            Toxicity score (0.0 to 1.0)
        
        Returns
        -------
        ModerationAction
            Recommended moderation action
        """
        for action, (min_score, max_score) in self.thresholds.items():
            if min_score <= score < max_score:
                return action
        
        # If score >= 1.0, return BLOCK
        return ModerationAction.BLOCK
    
    def get_severity_for_score(self, score: float) -> SeverityLevel:
        """
        Determine severity level based on score.
        
        Parameters
        ----------
        score : float
            Toxicity score (0.0 to 1.0)
        
        Returns
        -------
        SeverityLevel
            Severity level
        """
        # Sort severity levels by threshold (descending)
        sorted_levels = sorted(
            self.severity_thresholds.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        for level, threshold in sorted_levels:
            if score >= threshold:
                return level
        
        return SeverityLevel.NONE
    
    def is_critical_label(self, label: str, score: float) -> bool:
        """
        Check if a label should trigger critical severity.
        
        Parameters
        ----------
        label : str
            Toxicity label name
        score : float
            Prediction score for this label
        
        Returns
        -------
        bool
            True if this label triggers critical severity
        """
        return label in self.critical_labels and score >= 0.7
    
    def get_weighted_score(self, label: str, score: float) -> float:
        """
        Apply label weight to score.
        
        Parameters
        ----------
        label : str
            Toxicity label name
        score : float
            Raw prediction score
        
        Returns
        -------
        float
            Weighted score (capped at 1.0)
        """
        weight = self.label_weights.get(label, 1.0)
        weighted = score * weight
        return min(weighted, 1.0)  # Cap at 1.0
    
    def aggregate_scores(
        self,
        predictions: Dict[str, float]
    ) -> Tuple[float, str]:
        """
        Aggregate multi-label predictions into a single score.
        
        Parameters
        ----------
        predictions : Dict[str, float]
            Dictionary of label -> score predictions
        
        Returns
        -------
        Tuple[float, str]
            (aggregated_score, primary_label)
        """
        if not predictions:
            return 0.0, "none"
        
        if self.aggregation_strategy == "max":
            # Simple max score
            primary_label = max(predictions, key=predictions.get)
            return predictions[primary_label], primary_label
        
        elif self.aggregation_strategy == "weighted_max":
            # Apply weights and take max
            weighted_scores = {
                label: self.get_weighted_score(label, score)
                for label, score in predictions.items()
            }
            primary_label = max(weighted_scores, key=weighted_scores.get)
            return weighted_scores[primary_label], primary_label
        
        elif self.aggregation_strategy == "average":
            # Average of all scores above threshold
            significant_scores = [
                score for score in predictions.values()
                if score >= self.min_confidence
            ]
            if significant_scores:
                avg_score = sum(significant_scores) / len(significant_scores)
                primary_label = max(predictions, key=predictions.get)
                return avg_score, primary_label
            else:
                return 0.0, "none"
        
        else:
            raise ValueError(f"Unknown aggregation strategy: {self.aggregation_strategy}")
    
    def to_dict(self) -> Dict:
        """
        Export rules configuration as dictionary.
        
        Returns
        -------
        dict
            Configuration dictionary
        """
        return {
            'thresholds': {
                action.value: (min_val, max_val)
                for action, (min_val, max_val) in self.thresholds.items()
            },
            'severity_thresholds': {
                level.value: threshold
                for level, threshold in self.severity_thresholds.items()
            },
            'label_weights': self.label_weights,
            'critical_labels': self.critical_labels,
            'min_confidence': self.min_confidence,
            'aggregation_strategy': self.aggregation_strategy
        }
    
    @classmethod
    def from_dict(cls, config: Dict) -> 'ModerationRules':
        """
        Create ModerationRules from configuration dictionary.
        
        Parameters
        ----------
        config : dict
            Configuration dictionary
        
        Returns
        -------
        ModerationRules
            Configured rules instance
        """
        # Convert string keys back to enums
        thresholds = {
            ModerationAction(action): (min_val, max_val)
            for action, (min_val, max_val) in config.get('thresholds', {}).items()
        }
        
        severity_thresholds = {
            SeverityLevel(level): threshold
            for level, threshold in config.get('severity_thresholds', {}).items()
        }
        
        return cls(
            thresholds=thresholds if thresholds else cls().thresholds,
            severity_thresholds=severity_thresholds if severity_thresholds else cls().severity_thresholds,
            label_weights=config.get('label_weights', cls().label_weights),
            critical_labels=config.get('critical_labels', cls().critical_labels),
            min_confidence=config.get('min_confidence', cls().min_confidence),
            aggregation_strategy=config.get('aggregation_strategy', cls().aggregation_strategy)
        )


# Predefined rule configurations for different use cases
class PresetRules:
    """
    Predefined moderation rule configurations for common use cases.
    """
    
    @staticmethod
    def strict() -> ModerationRules:
        """
        Strict moderation rules (low tolerance for toxicity).
        Suitable for: Family-friendly platforms, educational content
        """
        rules = ModerationRules()
        rules.thresholds = {
            ModerationAction.ALLOW: (0.0, 0.2),
            ModerationAction.WARNING: (0.2, 0.4),
            ModerationAction.HIDE: (0.4, 0.6),
            ModerationAction.BLOCK: (0.6, 1.0)
        }
        rules.min_confidence = 0.4
        return rules
    
    @staticmethod
    def moderate() -> ModerationRules:
        """
        Moderate moderation rules (balanced approach).
        Suitable for: General social media, forums, comment sections
        """
        return ModerationRules()  # Default rules are moderate
    
    @staticmethod
    def lenient() -> ModerationRules:
        """
        Lenient moderation rules (high tolerance for toxicity).
        Suitable for: Adult content platforms, debate forums
        """
        rules = ModerationRules()
        rules.thresholds = {
            ModerationAction.ALLOW: (0.0, 0.5),
            ModerationAction.WARNING: (0.5, 0.7),
            ModerationAction.HIDE: (0.7, 0.85),
            ModerationAction.BLOCK: (0.85, 1.0)
        }
        rules.min_confidence = 0.6
        return rules
    
    @staticmethod
    def zero_tolerance() -> ModerationRules:
        """
        Zero tolerance rules (block anything suspicious).
        Suitable for: Children's platforms, highly regulated environments
        """
        rules = ModerationRules()
        rules.thresholds = {
            ModerationAction.ALLOW: (0.0, 0.1),
            ModerationAction.WARNING: (0.1, 0.2),
            ModerationAction.HIDE: (0.2, 0.3),
            ModerationAction.BLOCK: (0.3, 1.0)
        }
        rules.min_confidence = 0.3
        rules.critical_labels = ['threat', 'severe_toxic', 'identity_hate', 'insult', 'obscene']
        return rules
