"""
Train DistilBERT on 10,000 samples (faster training for testing).

This script trains on a subset of the data:
- 10,000 samples total
- 7,000 train / 1,500 val / 1,500 test
- Expected time: 30-45 minutes on CPU
- Good for testing the full pipeline without waiting hours
"""

import sys
import logging
from src.training.train_bert import BERTTrainingPipeline, BERTConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def main():
    logger.info("=" * 70)
    logger.info("BERT TRAINING - 10K SAMPLES")
    logger.info("=" * 70)
    logger.info("\nThis will train on 10,000 samples (instead of 159k)")
    logger.info("Expected time: 30-45 minutes on CPU")
    logger.info("")
    
    # Initialize configuration
    config = BERTConfig()
    
    # Reduce epochs for faster training (optional - you can keep 3 if you want)
    config.num_epochs = 2  # Reduced from 3 to 2 for faster training
    
    # Initialize pipeline
    pipeline = BERTTrainingPipeline(config)
    
    # Load and prepare data
    train_df, val_df, test_df = pipeline.load_and_prepare_data()
    
    # ⚠️ REDUCE DATASET SIZE TO 10K SAMPLES
    logger.info("\n⚠️  REDUCING DATASET SIZE TO 10K SAMPLES")
    train_df = train_df.head(7000)
    val_df = val_df.head(1500)
    test_df = test_df.head(1500)
    logger.info(f"  Train: {len(train_df):,} samples")
    logger.info(f"  Val:   {len(val_df):,} samples")
    logger.info(f"  Test:  {len(test_df):,} samples")
    
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
    logger.info("TRAINING COMPLETE - 10K SAMPLES")
    logger.info("=" * 70)
    logger.info(f"\nKey Results:")
    logger.info(f"  Test Accuracy:  {results['overall']['accuracy']:.4f}")
    logger.info(f"  Test F1 (micro): {results['overall']['f1_micro']:.4f}")
    logger.info(f"  Test F1 (macro): {results['overall']['f1_macro']:.4f}")
    logger.info("\nNote: Results may be slightly lower than full training")
    logger.info("      because we used only 10k samples instead of 159k")
    logger.info("\nArtifacts saved:")
    logger.info(f"  - {config.final_model_dir}")
    logger.info(f"  - {config.tokenizer_dir}")
    logger.info(f"  - {config.checkpoint_dir}")
    logger.info(f"  - results/bert_metrics.json")
    logger.info("\nYou can now test inference:")
    logger.info("  python src/inference/bert_predict.py --examples")


if __name__ == '__main__':
    main()
