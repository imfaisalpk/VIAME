#!/bin/sh

# Input locations and types
export INPUT_DIRECTORY=training_data_mouss

# Path to VIAME installation
export VIAME_INSTALL="$(cd "$(dirname ${BASH_SOURCE[0]})" && pwd)/../.."

source ${VIAME_INSTALL}/setup_viame.sh 

# Run pipeline
viame_train_detector \
  -i ${INPUT_DIRECTORY} \
  -c ${VIAME_INSTALL}/configs/pipelines/train_yolo_704.viame_csv.conf \
  --threshold 0.0
