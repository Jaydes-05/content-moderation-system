"""
Quick test script for BERT training pipeline.

This script trains on a tiny subset (1000 samples) to verify
everything works without waiting hours for full training.

Usage:
    python test_bert_quick.py
"""

import os
import sys
import logging

# Add src to path
sys.path.insert(0, 'src')

from training.train_bert import BERTConfig, BERTTrainingPipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("=" * 70)
    logger.info("QUICK TEST - BERT TRAINING (1000 samples)")
    logger.info("=" * 70)
    logger.info("\nThis is a quick test to verify the pipeline works.")
    logger.info("It will train on only 1000 samples for 1 epoch.")
    logger.info("Expected time: 5-10 minutes on CPU\n")
    
    # Create config with reduced settings
    config = BERTConfig()
    config.num_epochs = 1  # Just 1 epoch for testing
    config.train_batch_size = 8  # Smaller batch for CPU
    config.eval_batch_size = 16
    config.logging_steps = 50
    config.save_strategy = "no"  # Don't save checkpoints for test
    config.load_best_model_at_end = False  # Can't load best if not saving
    
    # Initialize pipeline
    pipeline = BERTTrainingPipeline(config)
    
    # Load and prepare data
    train_df, val_df, test_df = pipeline.load_and_prepare_data()
    
    # Use only 1000 samples for quick test
    logger.info("\n⚠️  REDUCING DATASET SIZE FOR QUICK TEST")
    train_df = train_df.head(800)
    val_df = val_df.head(100)
    test_df = test_df.head(100)
    logger.info(f"  Train: {len(train_df)} samples")
    logger.info(f"  Val:   {len(val_df)} samples")
    logger.info(f"  Test:  {len(test_df)} samples")
    
    # Initialize model and tokenizer
    pipeline.initialize_model_and_tokenizer()
    
    # Create datasets
    pipeline.create_datasets(train_df, val_df, test_df)
    
    # Train
    logger.info("\n" + "=" * 70)
    logger.info("STARTING TRAINING (this will take 5-10 minutes)")
    logger.info("=" * 70)
    pipeline.train()
    
    # Evaluate
    results = pipeline.evaluate()
    
    # Print results
    logger.info("\n" + "=" * 70)
    logger.info("QUICK TEST COMPLETE")
    logger.info("=" * 70)
    logger.info(f"\nResults on 100 test samples:")
    logger.info(f"  Accuracy:  {results['overall']['accuracy']:.4f}")
    logger.info(f"  F1 (micro): {results['overall']['f1_micro']:.4f}")
    logger.info(f"  F1 (macro): {results['overall']['f1_macro']:.4f}")
    
    logger.info("\n✓ Pipeline works! You can now train on full dataset.")
    logger.info("  Run: python src/training/train_bert.py")

if __name__ == '__main__':
    main()
