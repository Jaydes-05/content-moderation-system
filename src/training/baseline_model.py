"""
Baseline multi-label toxicity classification using TF-IDF + Logistic Regression.

This module provides a baseline model for content moderation using traditional
machine learning approaches. It serves as a performance benchmark before
implementing more complex transformer-based models.

Architecture:
    - TF-IDF Vectorizer for text representation
    - OneVsRestClassifier with Logistic Regression for multi-label classification
    - Handles 6 toxicity labels: toxic, severe_toxic, obscene, threat, insult, identity_hate

Usage:
    from training.baseline_model import BaselineClassifier
    
    classifier = BaselineClassifier()
    classifier.train(X_train, y_train)
    metrics = classifier.evaluate(X_test, y_test)
    classifier.save_artifacts()
"""

import os
import json
import pickle
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    multilabel_confusion_matrix,
    hamming_loss,
    jaccard_score
)

# ── Configure logging ───────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class BaselineClassifier:
    """
    Baseline multi-label toxicity classifier using TF-IDF + Logistic Regression.
    
    This class encapsulates the entire baseline modeling pipeline including:
    - Text vectorization using TF-IDF
    - Multi-label classification using OneVsRestClassifier
    - Model evaluation with comprehensive metrics
    - Artifact persistence for deployment
    
    Attributes
    ----------
    label_cols : List[str]
        Names of the toxicity label columns
    vectorizer : TfidfVectorizer
        Fitted TF-IDF vectorizer
    model : OneVsRestClassifier
        Fitted multi-label classifier
    metrics : Dict
        Evaluation metrics from the test set
    
    Parameters
    ----------
    max_features : int, default=10000
        Maximum number of TF-IDF features
    ngram_range : Tuple[int, int], default=(1, 2)
        N-gram range for TF-IDF (unigrams + bigrams)
    min_df : int, default=5
        Minimum document frequency for TF-IDF
    max_df : float, default=0.8
        Maximum document frequency for TF-IDF
    C : float, default=4.0
        Inverse regularization strength for Logistic Regression
    random_state : int, default=42
        Random seed for reproducibility
    """
    
    def __init__(
        self,
        max_features: int = 10000,
        ngram_range: Tuple[int, int] = (1, 2),
        min_df: int = 5,
        max_df: float = 0.8,
        C: float = 4.0,
        random_state: int = 42
    ):
        self.label_cols = [
            'toxic', 'severe_toxic', 'obscene',
            'threat', 'insult', 'identity_hate'
        ]
        
        # TF-IDF configuration
        self.max_features = max_features
        self.ngram_range = ngram_range
        self.min_df = min_df
        self.max_df = max_df
        
        # Model configuration
        self.C = C
        self.random_state = random_state
        
        # Initialize components
        self.vectorizer = None
        self.model = None
        self.metrics = {}
        
        logger.info("BaselineClassifier initialized")
        logger.info(f"  TF-IDF: max_features={max_features}, ngram_range={ngram_range}")
        logger.info(f"  LogReg: C={C}, random_state={random_state}")
    
    def _create_vectorizer(self) -> TfidfVectorizer:
        """Create and configure TF-IDF vectorizer."""
        return TfidfVectorizer(
            max_features=self.max_features,
            ngram_range=self.ngram_range,
            min_df=self.min_df,
            max_df=self.max_df,
            strip_accents='unicode',
            lowercase=True,
            analyzer='word',
            token_pattern=r'\w{1,}',
            use_idf=True,
            smooth_idf=True,
            sublinear_tf=True
        )
    
    def _create_model(self) -> OneVsRestClassifier:
        """Create and configure multi-label classifier."""
        base_estimator = LogisticRegression(
            C=self.C,
            solver='lbfgs',
            max_iter=1000,
            random_state=self.random_state,
            n_jobs=-1,
            class_weight='balanced'  # Handle class imbalance
        )
        return OneVsRestClassifier(base_estimator, n_jobs=-1)
    
    def train(
        self,
        X_train: pd.Series,
        y_train: pd.DataFrame,
        verbose: bool = True
    ) -> 'BaselineClassifier':
        """
        Train the baseline classifier.
        
        Parameters
        ----------
        X_train : pd.Series
            Training text data (preprocessed comments)
        y_train : pd.DataFrame
            Training labels (multi-label binary matrix)
        verbose : bool, default=True
            Whether to print training progress
        
        Returns
        -------
        self : BaselineClassifier
            Fitted classifier instance
        """
        logger.info("=" * 70)
        logger.info("TRAINING BASELINE CLASSIFIER")
        logger.info("=" * 70)
        
        # Validate inputs
        assert len(X_train) == len(y_train), "X_train and y_train must have same length"
        assert all(col in y_train.columns for col in self.label_cols), \
            f"y_train must contain columns: {self.label_cols}"
        
        logger.info(f"Training samples: {len(X_train):,}")
        logger.info(f"Label distribution:")
        for col in self.label_cols:
            count = y_train[col].sum()
            pct = count / len(y_train) * 100
            logger.info(f"  {col:15s}: {count:6,} ({pct:5.2f}%)")
        
        # Step 1: Fit TF-IDF vectorizer
        logger.info("\n[1/3] Fitting TF-IDF vectorizer...")
        self.vectorizer = self._create_vectorizer()
        X_train_tfidf = self.vectorizer.fit_transform(X_train)
        logger.info(f"  Vocabulary size: {len(self.vectorizer.vocabulary_):,}")
        logger.info(f"  Feature matrix shape: {X_train_tfidf.shape}")
        logger.info(f"  Sparsity: {(1 - X_train_tfidf.nnz / np.prod(X_train_tfidf.shape)) * 100:.2f}%")
        
        # Step 2: Train multi-label classifier
        logger.info("\n[2/3] Training OneVsRestClassifier...")
        self.model = self._create_model()
        self.model.fit(X_train_tfidf, y_train[self.label_cols])
        logger.info("  Training complete")
        
        # Step 3: Training set performance
        logger.info("\n[3/3] Evaluating on training set...")
        y_train_pred = self.model.predict(X_train_tfidf)
        train_accuracy = accuracy_score(y_train[self.label_cols], y_train_pred)
        train_f1_micro = f1_score(y_train[self.label_cols], y_train_pred, average='micro')
        train_f1_macro = f1_score(y_train[self.label_cols], y_train_pred, average='macro')
        
        logger.info(f"  Train Accuracy (exact match): {train_accuracy:.4f}")
        logger.info(f"  Train F1 (micro): {train_f1_micro:.4f}")
        logger.info(f"  Train F1 (macro): {train_f1_macro:.4f}")
        
        logger.info("\n" + "=" * 70)
        logger.info("TRAINING COMPLETE")
        logger.info("=" * 70)
        
        return self
    
    def predict(self, X: pd.Series) -> np.ndarray:
        """
        Predict toxicity labels for input text.
        
        Parameters
        ----------
        X : pd.Series
            Input text data (preprocessed comments)
        
        Returns
        -------
        predictions : np.ndarray
            Binary predictions of shape (n_samples, n_labels)
        """
        if self.vectorizer is None or self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        X_tfidf = self.vectorizer.transform(X)
        return self.model.predict(X_tfidf)
    
    def predict_proba(self, X: pd.Series) -> np.ndarray:
        """
        Predict toxicity probabilities for input text.
        
        Parameters
        ----------
        X : pd.Series
            Input text data (preprocessed comments)
        
        Returns
        -------
        probabilities : np.ndarray
            Probability predictions of shape (n_samples, n_labels)
        """
        if self.vectorizer is None or self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        X_tfidf = self.vectorizer.transform(X)
        
        # Get decision function scores (more reliable than predict_proba for OneVsRestClassifier)
        # Returns shape (n_samples, n_labels)
        decision_scores = self.model.decision_function(X_tfidf)
        
        # Convert to probabilities using sigmoid
        from scipy.special import expit
        probabilities = expit(decision_scores)
        
        return probabilities
    
    def evaluate(
        self,
        X_test: pd.Series,
        y_test: pd.DataFrame,
        verbose: bool = True
    ) -> Dict:
        """
        Evaluate the classifier on test data.
        
        Parameters
        ----------
        X_test : pd.Series
            Test text data (preprocessed comments)
        y_test : pd.DataFrame
            Test labels (multi-label binary matrix)
        verbose : bool, default=True
            Whether to print evaluation results
        
        Returns
        -------
        metrics : Dict
            Dictionary containing all evaluation metrics
        """
        logger.info("=" * 70)
        logger.info("EVALUATING BASELINE CLASSIFIER")
        logger.info("=" * 70)
        
        # Generate predictions
        logger.info(f"Test samples: {len(X_test):,}")
        y_pred = self.predict(X_test)
        y_proba = self.predict_proba(X_test)
        
        # Overall metrics
        accuracy = accuracy_score(y_test[self.label_cols], y_pred)
        precision_micro = precision_score(y_test[self.label_cols], y_pred, average='micro', zero_division=0)
        precision_macro = precision_score(y_test[self.label_cols], y_pred, average='macro', zero_division=0)
        recall_micro = recall_score(y_test[self.label_cols], y_pred, average='micro', zero_division=0)
        recall_macro = recall_score(y_test[self.label_cols], y_pred, average='macro', zero_division=0)
        f1_micro = f1_score(y_test[self.label_cols], y_pred, average='micro', zero_division=0)
        f1_macro = f1_score(y_test[self.label_cols], y_pred, average='macro', zero_division=0)
        hamming = hamming_loss(y_test[self.label_cols], y_pred)
        jaccard = jaccard_score(y_test[self.label_cols], y_pred, average='samples', zero_division=0)
        
        logger.info("\nOverall Metrics:")
        logger.info(f"  Accuracy (exact match): {accuracy:.4f}")
        logger.info(f"  Hamming Loss:           {hamming:.4f}")
        logger.info(f"  Jaccard Score:          {jaccard:.4f}")
        logger.info(f"\n  Precision (micro):      {precision_micro:.4f}")
        logger.info(f"  Precision (macro):      {precision_macro:.4f}")
        logger.info(f"  Recall (micro):         {recall_micro:.4f}")
        logger.info(f"  Recall (macro):         {recall_macro:.4f}")
        logger.info(f"  F1 (micro):             {f1_micro:.4f}")
        logger.info(f"  F1 (macro):             {f1_macro:.4f}")
        
        # Per-label metrics
        logger.info("\nPer-Label Metrics:")
        logger.info(f"{'Label':<15} {'Precision':>10} {'Recall':>10} {'F1-Score':>10} {'Support':>10}")
        logger.info("-" * 70)
        
        label_metrics = {}
        for i, label in enumerate(self.label_cols):
            y_true_label = y_test[label]
            y_pred_label = y_pred[:, i]
            
            prec = precision_score(y_true_label, y_pred_label, zero_division=0)
            rec = recall_score(y_true_label, y_pred_label, zero_division=0)
            f1 = f1_score(y_true_label, y_pred_label, zero_division=0)
            support = y_true_label.sum()
            
            logger.info(f"{label:<15} {prec:>10.4f} {rec:>10.4f} {f1:>10.4f} {support:>10,}")
            
            label_metrics[label] = {
                'precision': float(prec),
                'recall': float(rec),
                'f1_score': float(f1),
                'support': int(support)
            }
        
        # Confusion matrices
        conf_matrices = multilabel_confusion_matrix(y_test[self.label_cols], y_pred)
        
        logger.info("\nConfusion Matrices (per label):")
        for i, label in enumerate(self.label_cols):
            tn, fp, fn, tp = conf_matrices[i].ravel()
            logger.info(f"\n  {label}:")
            logger.info(f"    TN: {tn:6,}  FP: {fp:6,}")
            logger.info(f"    FN: {fn:6,}  TP: {tp:6,}")
        
        # Store metrics
        self.metrics = {
            'timestamp': datetime.now().isoformat(),
            'model_type': 'baseline_tfidf_logistic',
            'test_samples': len(X_test),
            'overall': {
                'accuracy': float(accuracy),
                'hamming_loss': float(hamming),
                'jaccard_score': float(jaccard),
                'precision_micro': float(precision_micro),
                'precision_macro': float(precision_macro),
                'recall_micro': float(recall_micro),
                'recall_macro': float(recall_macro),
                'f1_micro': float(f1_micro),
                'f1_macro': float(f1_macro)
            },
            'per_label': label_metrics,
            'confusion_matrices': {
                label: {
                    'tn': int(conf_matrices[i].ravel()[0]),
                    'fp': int(conf_matrices[i].ravel()[1]),
                    'fn': int(conf_matrices[i].ravel()[2]),
                    'tp': int(conf_matrices[i].ravel()[3])
                }
                for i, label in enumerate(self.label_cols)
            },
            'hyperparameters': {
                'max_features': self.max_features,
                'ngram_range': self.ngram_range,
                'min_df': self.min_df,
                'max_df': self.max_df,
                'C': self.C,
                'random_state': self.random_state
            }
        }
        
        logger.info("\n" + "=" * 70)
        logger.info("EVALUATION COMPLETE")
        logger.info("=" * 70)
        
        return self.metrics
    
    def save_artifacts(
        self,
        model_dir: str = 'models/baseline',
        results_dir: str = 'results'
    ) -> None:
        """
        Save trained model artifacts and evaluation metrics.
        
        Parameters
        ----------
        model_dir : str, default='models/baseline'
            Directory to save model artifacts
        results_dir : str, default='results'
            Directory to save evaluation metrics
        """
        logger.info("=" * 70)
        logger.info("SAVING ARTIFACTS")
        logger.info("=" * 70)
        
        # Create directories
        os.makedirs(model_dir, exist_ok=True)
        os.makedirs(results_dir, exist_ok=True)
        
        # Save vectorizer
        vectorizer_path = os.path.join(model_dir, 'tfidf_vectorizer.pkl')
        with open(vectorizer_path, 'wb') as f:
            pickle.dump(self.vectorizer, f)
        logger.info(f"✓ Saved TF-IDF vectorizer: {vectorizer_path}")
        
        # Save model
        model_path = os.path.join(model_dir, 'logistic_model.pkl')
        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)
        logger.info(f"✓ Saved Logistic Regression model: {model_path}")
        
        # Save metrics
        if self.metrics:
            metrics_path = os.path.join(results_dir, 'baseline_metrics.json')
            with open(metrics_path, 'w') as f:
                json.dump(self.metrics, f, indent=2)
            logger.info(f"✓ Saved evaluation metrics: {metrics_path}")
        
        logger.info("\n" + "=" * 70)
        logger.info("ARTIFACTS SAVED SUCCESSFULLY")
        logger.info("=" * 70)
    
    @classmethod
    def load_artifacts(
        cls,
        model_dir: str = 'models/baseline'
    ) -> 'BaselineClassifier':
        """
        Load trained model artifacts.
        
        Parameters
        ----------
        model_dir : str, default='models/baseline'
            Directory containing model artifacts
        
        Returns
        -------
        classifier : BaselineClassifier
            Loaded classifier instance
        """
        logger.info(f"Loading artifacts from: {model_dir}")
        
        classifier = cls()
        
        # Load vectorizer
        vectorizer_path = os.path.join(model_dir, 'tfidf_vectorizer.pkl')
        with open(vectorizer_path, 'rb') as f:
            classifier.vectorizer = pickle.load(f)
        logger.info(f"✓ Loaded TF-IDF vectorizer")
        
        # Load model
        model_path = os.path.join(model_dir, 'logistic_model.pkl')
        with open(model_path, 'rb') as f:
            classifier.model = pickle.load(f)
        logger.info(f"✓ Loaded Logistic Regression model")
        
        return classifier


# ═══════════════════════════════════════════════════════════════════════════
# Main Training Pipeline
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """
    Main training pipeline for baseline classifier.
    
    This function:
    1. Loads the cleaned dataset
    2. Applies preprocessing
    3. Splits into train/test sets
    4. Trains the baseline classifier
    5. Evaluates performance
    6. Saves artifacts
    """
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from preprocessing import preprocess_pipeline
    
    logger.info("=" * 70)
    logger.info("BASELINE TOXICITY CLASSIFICATION PIPELINE")
    logger.info("=" * 70)
    
    # ── Load dataset ────────────────────────────────────────────────────────
    logger.info("\n[1/6] Loading dataset...")
    data_path = 'data/processed/train_cleaned.csv'
    df = pd.read_csv(data_path)
    logger.info(f"  Loaded {len(df):,} samples from {data_path}")
    
    # ── Preprocess text ─────────────────────────────────────────────────────
    logger.info("\n[2/6] Preprocessing text...")
    df['comment_preprocessed'] = df['comment_text'].apply(
        lambda x: preprocess_pipeline(x, mode='ml')
    )
    
    # Remove empty comments
    df = df[df['comment_preprocessed'].str.len() > 0].reset_index(drop=True)
    logger.info(f"  Preprocessed {len(df):,} samples (removed empty comments)")
    
    # ── Prepare features and labels ─────────────────────────────────────────
    logger.info("\n[3/6] Preparing features and labels...")
    label_cols = ['toxic', 'severe_toxic', 'obscene', 'threat', 'insult', 'identity_hate']
    
    X = df['comment_preprocessed']
    y = df[label_cols]
    
    logger.info(f"  Features: {len(X):,} text samples")
    logger.info(f"  Labels: {y.shape[1]} toxicity categories")
    
    # ── Train/test split ────────────────────────────────────────────────────
    logger.info("\n[4/6] Splitting dataset...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42,
        stratify=y['toxic']  # Stratify on most common label
    )
    
    logger.info(f"  Train: {len(X_train):,} samples ({len(X_train)/len(X)*100:.1f}%)")
    logger.info(f"  Test:  {len(X_test):,} samples ({len(X_test)/len(X)*100:.1f}%)")
    
    # ── Train classifier ────────────────────────────────────────────────────
    logger.info("\n[5/6] Training baseline classifier...")
    classifier = BaselineClassifier(
        max_features=10000,
        ngram_range=(1, 2),
        min_df=5,
        max_df=0.8,
        C=4.0,
        random_state=42
    )
    
    classifier.train(X_train, y_train)
    
    # ── Evaluate ────────────────────────────────────────────────────────────
    logger.info("\n[6/6] Evaluating on test set...")
    metrics = classifier.evaluate(X_test, y_test)
    
    # ── Save artifacts ──────────────────────────────────────────────────────
    classifier.save_artifacts()
    
    logger.info("\n" + "=" * 70)
    logger.info("PIPELINE COMPLETE")
    logger.info("=" * 70)
    logger.info(f"\nKey Results:")
    logger.info(f"  Test Accuracy:  {metrics['overall']['accuracy']:.4f}")
    logger.info(f"  Test F1 (micro): {metrics['overall']['f1_micro']:.4f}")
    logger.info(f"  Test F1 (macro): {metrics['overall']['f1_macro']:.4f}")
    logger.info("\nArtifacts saved:")
    logger.info("  - models/baseline/tfidf_vectorizer.pkl")
    logger.info("  - models/baseline/logistic_model.pkl")
    logger.info("  - results/baseline_metrics.json")


if __name__ == '__main__':
    main()
