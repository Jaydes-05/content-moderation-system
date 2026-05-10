"""
Production-grade DistilBERT training pipeline for multi-label toxicity classification.

This module implements a complete transformer-based training pipeline using:
- DistilBERT (distilbert-base-uncased)
- PyTorch backend
- Hugging Face Transformers Trainer API
- Multi-label classification with sigmoid activation
- BCEWithLogitsLoss

Architecture:
    Input Text → DistilBERT Tokenizer → DistilBERT Model → Sigmoid → 6 Binary Predictions

Labels (independent, multi-label):
    toxic, severe_toxic, obscene, threat, insult, identity_hate

Usage:
    python src/training/train_bert.py
"""

import os
import sys
import json
import logging
import warnings
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    classification_report,
    multilabel_confusion_matrix
)

from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback
)

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from preprocessing import preprocess_pipeline

# Suppress warnings
warnings.filterwarnings('ignore')
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

# ── Configure logging ───────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class BERTConfig:
    """Configuration for DistilBERT training pipeline."""
    
    # Model configuration
    model_name: str = "distilbert-base-uncased"
    num_labels: int = 6
    problem_type: str = "multi_label_classification"
    
    # Tokenization
    max_length: int = 128
    truncation: bool = True
    padding: str = "max_length"
    
    # Training hyperparameters
    num_epochs: int = 3
    learning_rate: float = 2e-5
    train_batch_size: int = 16
    eval_batch_size: int = 32
    weight_decay: float = 0.01
    warmup_steps: int = 500
    
    # Data split
    test_size: float = 0.2
    val_size: float = 0.1  # From training set
    random_state: int = 42
    
    # Paths
    data_path: str = "data/processed/train_cleaned.csv"
    output_dir: str = "models/bert"
    checkpoint_dir: str = "models/bert/checkpoints"
    final_model_dir: str = "models/bert/final_model"
    tokenizer_dir: str = "models/bert/tokenizer"
    results_dir: str = "results"
    
    # Training settings
    save_strategy: str = "epoch"
    evaluation_strategy: str = "epoch"
    load_best_model_at_end: bool = True
    metric_for_best_model: str = "f1_macro"
    greater_is_better: bool = True
    save_total_limit: int = 2
    
    # Logging
    logging_steps: int = 100
    
    # Device
    device: str = field(default_factory=lambda: "cuda" if torch.cuda.is_available() else "cpu")
    
    # Labels (CRITICAL: maintain order)
    label_cols: List[str] = field(default_factory=lambda: [
        'toxic', 'severe_toxic', 'obscene', 'threat', 'insult', 'identity_hate'
    ])


# ═══════════════════════════════════════════════════════════════════════════
# Dataset Class
# ═══════════════════════════════════════════════════════════════════════════

class ToxicityDataset(Dataset):
    """
    PyTorch Dataset for multi-label toxicity classification.
    
    This dataset handles tokenization and label encoding for the
    DistilBERT model with multi-label classification.
    
    Parameters
    ----------
    texts : List[str]
        List of input texts
    labels : np.ndarray
        Multi-label binary matrix of shape (n_samples, n_labels)
    tokenizer : AutoTokenizer
        Hugging Face tokenizer
    max_length : int
        Maximum sequence length for tokenization
    """
    
    def __init__(
        self,
        texts: List[str],
        labels: np.ndarray,
        tokenizer: AutoTokenizer,
        max_length: int = 128
    ):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self) -> int:
        return len(self.texts)
    
    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        """
        Get a single tokenized sample with labels.
        
        Returns
        -------
        dict
            Dictionary with input_ids, attention_mask, and labels
        """
        text = str(self.texts[idx])
        label = self.labels[idx]
        
        # Tokenize
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.FloatTensor(label)
        }


# ═══════════════════════════════════════════════════════════════════════════
# Metrics Computation
# ═══════════════════════════════════════════════════════════════════════════

def compute_metrics(eval_pred) -> Dict[str, float]:
    """
    Compute evaluation metrics for multi-label classification.
    
    This function is used by the Trainer API during evaluation.
    It applies sigmoid to logits and computes precision, recall, F1, and accuracy.
    
    Parameters
    ----------
    eval_pred : EvalPrediction
        Predictions and labels from the model
    
    Returns
    -------
    dict
        Dictionary of metric names and values
    """
    logits, labels = eval_pred
    
    # Apply sigmoid to get probabilities
    predictions = torch.sigmoid(torch.tensor(logits)).numpy()
    
    # Convert probabilities to binary predictions (threshold=0.5)
    predictions = (predictions > 0.5).astype(int)
    
    # Compute metrics
    precision_micro, recall_micro, f1_micro, _ = precision_recall_fscore_support(
        labels, predictions, average='micro', zero_division=0
    )
    
    precision_macro, recall_macro, f1_macro, _ = precision_recall_fscore_support(
        labels, predictions, average='macro', zero_division=0
    )
    
    # Exact match accuracy (all labels must match)
    accuracy = accuracy_score(labels, predictions)
    
    return {
        'accuracy': accuracy,
        'precision_micro': precision_micro,
        'precision_macro': precision_macro,
        'recall_micro': recall_micro,
        'recall_macro': recall_macro,
        'f1_micro': f1_micro,
        'f1_macro': f1_macro
    }


# ═══════════════════════════════════════════════════════════════════════════
# Training Pipeline
# ═══════════════════════════════════════════════════════════════════════════

class BERTTrainingPipeline:
    """
    Complete training pipeline for DistilBERT toxicity classifier.
    
    This class encapsulates the entire training workflow including:
    - Data loading and preprocessing
    - Model initialization
    - Training with Trainer API
    - Evaluation and metrics
    - Model saving
    
    Parameters
    ----------
    config : BERTConfig
        Configuration object with all hyperparameters
    """
    
    def __init__(self, config: BERTConfig):
        self.config = config
        self.tokenizer = None
        self.model = None
        self.trainer = None
        self.train_dataset = None
        self.val_dataset = None
        self.test_dataset = None
        
        # Create output directories
        os.makedirs(config.output_dir, exist_ok=True)
        os.makedirs(config.checkpoint_dir, exist_ok=True)
        os.makedirs(config.final_model_dir, exist_ok=True)
        os.makedirs(config.tokenizer_dir, exist_ok=True)
        os.makedirs(config.results_dir, exist_ok=True)
        
        logger.info(f"Initialized BERTTrainingPipeline")
        logger.info(f"Device: {config.device}")
        logger.info(f"Model: {config.model_name}")
    
    def load_and_prepare_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Load dataset and split into train/val/test sets.
        
        Returns
        -------
        tuple
            (train_df, val_df, test_df)
        """
        logger.info("=" * 70)
        logger.info("LOADING AND PREPARING DATA")
        logger.info("=" * 70)
        
        # Load dataset
        logger.info(f"Loading dataset from: {self.config.data_path}")
        df = pd.read_csv(self.config.data_path)
        logger.info(f"Loaded {len(df):,} samples")
        
        # Validate required columns
        required_cols = ['comment_text'] + self.config.label_cols
        missing_cols = set(required_cols) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Handle null text safely
        df['comment_text'] = df['comment_text'].fillna('')
        
        # Apply lightweight preprocessing (transformer mode)
        logger.info("Applying lightweight preprocessing...")
        df['text_clean'] = df['comment_text'].apply(
            lambda x: preprocess_pipeline(x, mode='transformer')
        )
        
        # Remove empty texts
        df = df[df['text_clean'].str.len() > 0].reset_index(drop=True)
        logger.info(f"After preprocessing: {len(df):,} samples")
        
        # Prepare features and labels
        X = df['text_clean'].tolist()
        y = df[self.config.label_cols].values
        
        # Log label distribution
        logger.info("\nLabel distribution:")
        for i, label in enumerate(self.config.label_cols):
            count = y[:, i].sum()
            pct = count / len(y) * 100
            logger.info(f"  {label:15s}: {count:6,} ({pct:5.2f}%)")
        
        # Split: train/test first
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=self.config.test_size,
            random_state=self.config.random_state,
            stratify=y[:, 0]  # Stratify on 'toxic' label
        )
        
        # Split train into train/val
        val_size_adjusted = self.config.val_size / (1 - self.config.test_size)
        X_train, X_val, y_train, y_val = train_test_split(
            X_train, y_train,
            test_size=val_size_adjusted,
            random_state=self.config.random_state,
            stratify=y_train[:, 0]
        )
        
        logger.info(f"\nData split:")
        logger.info(f"  Train: {len(X_train):,} samples ({len(X_train)/len(X)*100:.1f}%)")
        logger.info(f"  Val:   {len(X_val):,} samples ({len(X_val)/len(X)*100:.1f}%)")
        logger.info(f"  Test:  {len(X_test):,} samples ({len(X_test)/len(X)*100:.1f}%)")
        
        # Create DataFrames
        train_df = pd.DataFrame({'text': X_train, 'labels': list(y_train)})
        val_df = pd.DataFrame({'text': X_val, 'labels': list(y_val)})
        test_df = pd.DataFrame({'text': X_test, 'labels': list(y_test)})
        
        return train_df, val_df, test_df
    
    def initialize_model_and_tokenizer(self):
        """Initialize DistilBERT model and tokenizer."""
        logger.info("\n" + "=" * 70)
        logger.info("INITIALIZING MODEL AND TOKENIZER")
        logger.info("=" * 70)
        
        # Load tokenizer
        logger.info(f"Loading tokenizer: {self.config.model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(self.config.model_name)
        logger.info("✓ Tokenizer loaded")
        
        # Load model
        logger.info(f"Loading model: {self.config.model_name}")
        self.model = AutoModelForSequenceClassification.from_pretrained(
            self.config.model_name,
            num_labels=self.config.num_labels,
            problem_type=self.config.problem_type
        )
        
        # Move to device
        self.model.to(self.config.device)
        logger.info(f"✓ Model loaded and moved to {self.config.device}")
        
        # Log model info
        num_params = sum(p.numel() for p in self.model.parameters())
        num_trainable = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        logger.info(f"  Total parameters: {num_params:,}")
        logger.info(f"  Trainable parameters: {num_trainable:,}")
    
    def create_datasets(
        self,
        train_df: pd.DataFrame,
        val_df: pd.DataFrame,
        test_df: pd.DataFrame
    ):
        """Create PyTorch datasets for train/val/test."""
        logger.info("\n" + "=" * 70)
        logger.info("CREATING PYTORCH DATASETS")
        logger.info("=" * 70)
        
        self.train_dataset = ToxicityDataset(
            texts=train_df['text'].tolist(),
            labels=np.array(train_df['labels'].tolist()),
            tokenizer=self.tokenizer,
            max_length=self.config.max_length
        )
        
        self.val_dataset = ToxicityDataset(
            texts=val_df['text'].tolist(),
            labels=np.array(val_df['labels'].tolist()),
            tokenizer=self.tokenizer,
            max_length=self.config.max_length
        )
        
        self.test_dataset = ToxicityDataset(
            texts=test_df['text'].tolist(),
            labels=np.array(test_df['labels'].tolist()),
            tokenizer=self.tokenizer,
            max_length=self.config.max_length
        )
        
        logger.info(f"✓ Train dataset: {len(self.train_dataset):,} samples")
        logger.info(f"✓ Val dataset:   {len(self.val_dataset):,} samples")
        logger.info(f"✓ Test dataset:  {len(self.test_dataset):,} samples")
    
    def train(self):
        """Train the model using Hugging Face Trainer API."""
        logger.info("\n" + "=" * 70)
        logger.info("TRAINING DISTILBERT MODEL")
        logger.info("=" * 70)
        
        # Warn about CPU training
        if self.config.device == 'cpu':
            logger.warning("⚠️  Training on CPU - this will be VERY SLOW!")
            logger.warning("⚠️  Expected training time: 3-4 hours")
            logger.warning("⚠️  Consider using GPU or reducing dataset size for testing")
            logger.warning("⚠️  To use GPU: Install CUDA-enabled PyTorch")
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=self.config.checkpoint_dir,
            num_train_epochs=self.config.num_epochs,
            learning_rate=self.config.learning_rate,
            per_device_train_batch_size=self.config.train_batch_size,
            per_device_eval_batch_size=self.config.eval_batch_size,
            weight_decay=self.config.weight_decay,
            warmup_steps=self.config.warmup_steps,
            
            # Evaluation and saving
            evaluation_strategy=self.config.evaluation_strategy,
            save_strategy=self.config.save_strategy,
            load_best_model_at_end=self.config.load_best_model_at_end,
            metric_for_best_model=self.config.metric_for_best_model,
            greater_is_better=self.config.greater_is_better,
            save_total_limit=self.config.save_total_limit,
            
            # Logging
            logging_dir=os.path.join(self.config.output_dir, 'logs'),
            logging_steps=self.config.logging_steps,
            
            # Performance (only enable fp16 on CUDA)
            fp16=torch.cuda.is_available() and self.config.device == 'cuda',
            dataloader_num_workers=0,
            
            # Reproducibility
            seed=self.config.random_state,
            
            # Disable unnecessary features
            report_to="none",
            push_to_hub=False,
            
            # Disable tqdm for cleaner output
            disable_tqdm=False
        )
        
        # Prepare callbacks
        callbacks = []
        if self.config.load_best_model_at_end:
            callbacks.append(EarlyStoppingCallback(early_stopping_patience=2))
        
        # Initialize Trainer
        self.trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=self.train_dataset,
            eval_dataset=self.val_dataset,
            compute_metrics=compute_metrics,
            callbacks=callbacks
        )
        
        # Log training configuration
        logger.info(f"\nTraining configuration:")
        logger.info(f"  Epochs: {self.config.num_epochs}")
        logger.info(f"  Learning rate: {self.config.learning_rate}")
        logger.info(f"  Train batch size: {self.config.train_batch_size}")
        logger.info(f"  Eval batch size: {self.config.eval_batch_size}")
        logger.info(f"  Weight decay: {self.config.weight_decay}")
        logger.info(f"  Warmup steps: {self.config.warmup_steps}")
        logger.info(f"  Max length: {self.config.max_length}")
        
        # Train
        logger.info("\nStarting training...")
        train_result = self.trainer.train()
        
        logger.info("\n" + "=" * 70)
        logger.info("TRAINING COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Training time: {train_result.metrics['train_runtime']:.2f}s")
        logger.info(f"Training samples/sec: {train_result.metrics['train_samples_per_second']:.2f}")
    
    def evaluate(self) -> Dict:
        """
        Evaluate the model on test set with comprehensive metrics.
        
        Returns
        -------
        dict
            Dictionary containing all evaluation metrics
        """
        logger.info("\n" + "=" * 70)
        logger.info("EVALUATING ON TEST SET")
        logger.info("=" * 70)
        
        # Get predictions
        predictions_output = self.trainer.predict(self.test_dataset)
        logits = predictions_output.predictions
        labels = predictions_output.label_ids
        
        # Apply sigmoid
        probs = torch.sigmoid(torch.tensor(logits)).numpy()
        preds = (probs > 0.5).astype(int)
        
        # Overall metrics
        precision_micro, recall_micro, f1_micro, _ = precision_recall_fscore_support(
            labels, preds, average='micro', zero_division=0
        )
        precision_macro, recall_macro, f1_macro, _ = precision_recall_fscore_support(
            labels, preds, average='macro', zero_division=0
        )
        accuracy = accuracy_score(labels, preds)
        
        logger.info("\nOverall Metrics:")
        logger.info(f"  Accuracy (exact match): {accuracy:.4f}")
        logger.info(f"  Precision (micro):      {precision_micro:.4f}")
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
        for i, label in enumerate(self.config.label_cols):
            y_true = labels[:, i]
            y_pred = preds[:, i]
            
            prec, rec, f1, _ = precision_recall_fscore_support(
                y_true, y_pred, average='binary', zero_division=0
            )
            support = y_true.sum()
            
            logger.info(f"{label:<15} {prec:>10.4f} {rec:>10.4f} {f1:>10.4f} {support:>10,}")
            
            label_metrics[label] = {
                'precision': float(prec),
                'recall': float(rec),
                'f1_score': float(f1),
                'support': int(support)
            }
        
        # Confusion matrices
        conf_matrices = multilabel_confusion_matrix(labels, preds)
        
        logger.info("\nConfusion Matrices (per label):")
        confusion_dict = {}
        for i, label in enumerate(self.config.label_cols):
            tn, fp, fn, tp = conf_matrices[i].ravel()
            logger.info(f"\n  {label}:")
            logger.info(f"    TN: {tn:6,}  FP: {fp:6,}")
            logger.info(f"    FN: {fn:6,}  TP: {tp:6,}")
            
            confusion_dict[label] = {
                'tn': int(tn), 'fp': int(fp),
                'fn': int(fn), 'tp': int(tp)
            }
        
        # Compile results
        results = {
            'model_type': 'distilbert-base-uncased',
            'test_samples': len(self.test_dataset),
            'overall': {
                'accuracy': float(accuracy),
                'precision_micro': float(precision_micro),
                'precision_macro': float(precision_macro),
                'recall_micro': float(recall_micro),
                'recall_macro': float(recall_macro),
                'f1_micro': float(f1_micro),
                'f1_macro': float(f1_macro)
            },
            'per_label': label_metrics,
            'confusion_matrices': confusion_dict,
            'hyperparameters': {
                'model_name': self.config.model_name,
                'num_epochs': self.config.num_epochs,
                'learning_rate': self.config.learning_rate,
                'batch_size': self.config.train_batch_size,
                'max_length': self.config.max_length,
                'weight_decay': self.config.weight_decay
            }
        }
        
        return results
    
    def save_model(self):
        """Save the trained model, tokenizer, and configuration."""
        logger.info("\n" + "=" * 70)
        logger.info("SAVING MODEL ARTIFACTS")
        logger.info("=" * 70)
        
        # Save model
        self.model.save_pretrained(self.config.final_model_dir)
        logger.info(f"✓ Model saved to: {self.config.final_model_dir}")
        
        # Save tokenizer
        self.tokenizer.save_pretrained(self.config.tokenizer_dir)
        logger.info(f"✓ Tokenizer saved to: {self.config.tokenizer_dir}")
        
        # Save config
        config_dict = {
            'model_name': self.config.model_name,
            'num_labels': self.config.num_labels,
            'label_cols': self.config.label_cols,
            'max_length': self.config.max_length,
            'problem_type': self.config.problem_type
        }
        
        config_path = os.path.join(self.config.final_model_dir, 'training_config.json')
        with open(config_path, 'w') as f:
            json.dump(config_dict, f, indent=2)
        logger.info(f"✓ Config saved to: {config_path}")
    
    def save_results(self, results: Dict):
        """Save evaluation results to JSON."""
        results_path = os.path.join(self.config.results_dir, 'bert_metrics.json')
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"✓ Results saved to: {results_path}")
    
    def run_sanity_tests(self):
        """Run sanity tests with example predictions."""
        logger.info("\n" + "=" * 70)
        logger.info("SANITY TESTS - SAMPLE PREDICTIONS")
        logger.info("=" * 70)
        
        test_cases = [
            ("Toxic - Insult", "You are an idiot and should be ashamed!"),
            ("Toxic - Threat", "I will kill you!"),
            ("Toxic - Multi-label", "You stupid f***ing idiot, go die!"),
            ("Clean - Positive", "This is a great article, thanks!"),
            ("Clean - Neutral", "I disagree with your opinion."),
        ]
        
        self.model.eval()
        
        for label, text in test_cases:
            # Preprocess
            text_clean = preprocess_pipeline(text, mode='transformer')
            
            # Tokenize
            inputs = self.tokenizer(
                text_clean,
                truncation=True,
                padding='max_length',
                max_length=self.config.max_length,
                return_tensors='pt'
            )
            
            # Move to device
            inputs = {k: v.to(self.config.device) for k, v in inputs.items()}
            
            # Predict
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probs = torch.sigmoid(logits).cpu().numpy()[0]
            
            # Display
            logger.info(f"\n[{label}]")
            logger.info(f"Text: {text}")
            logger.info("Predictions:")
            for i, (col, prob) in enumerate(zip(self.config.label_cols, probs)):
                if prob > 0.5:
                    logger.info(f"  ✓ {col:15s}: {prob:.4f}")


# ═══════════════════════════════════════════════════════════════════════════
# Main Execution
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """Main training pipeline execution."""
    logger.info("=" * 70)
    logger.info("DISTILBERT TOXICITY CLASSIFICATION TRAINING PIPELINE")
    logger.info("=" * 70)
    
    # Initialize configuration
    config = BERTConfig()
    
    # Initialize pipeline
    pipeline = BERTTrainingPipeline(config)
    
    # Load and prepare data
    train_df, val_df, test_df = pipeline.load_and_prepare_data()
    
    # Initialize model and tokenizer
    pipeline.initialize_model_and_tokenizer()
    
    # Create datasets
    pipeline.create_datasets(train_df, val_df, test_df)
    
    # Train
    pipeline.train()
    
    # Evaluate
    results = pipeline.evaluate()
    
    # Save model
    pipeline.save_model()
    
    # Save results
    pipeline.save_results(results)
    
    # Run sanity tests
    pipeline.run_sanity_tests()
    
    # Final summary
    logger.info("\n" + "=" * 70)
    logger.info("PIPELINE COMPLETE")
    logger.info("=" * 70)
    logger.info(f"\nKey Results:")
    logger.info(f"  Test Accuracy:  {results['overall']['accuracy']:.4f}")
    logger.info(f"  Test F1 (micro): {results['overall']['f1_micro']:.4f}")
    logger.info(f"  Test F1 (macro): {results['overall']['f1_macro']:.4f}")
    logger.info("\nArtifacts saved:")
    logger.info(f"  - {config.final_model_dir}")
    logger.info(f"  - {config.tokenizer_dir}")
    logger.info(f"  - {config.checkpoint_dir}")
    logger.info(f"  - {os.path.join(config.results_dir, 'bert_metrics.json')}")


if __name__ == '__main__':
    main()
