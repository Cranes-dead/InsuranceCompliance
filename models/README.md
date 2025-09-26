# Models Directory

This directory contains the trained machine learning models for the compliance system.

## What's Included in Git:
- `config.json` - Model configuration files
- `tokenizer*.json` - Tokenizer configurations  
- `special_tokens_map.json` - Token mappings
- `vocab.txt` - Vocabulary files
- `rule_type_labels.json` - Label mappings

## What's Excluded from Git (but required):
- `model.safetensors` - Large model weight files
- `pytorch_model.bin` - PyTorch model binaries
- `checkpoint-*/` - Training checkpoint directories
- `training_args.bin` - Training configuration binaries

## To Use:
The excluded large files are automatically downloaded/generated when:
1. Running the Legal BERT training script
2. Loading the compliance system for the first time

The system will work without the large model files, but will need to retrain or download them on first use.