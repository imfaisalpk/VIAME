# ckwg +29
# Copyright 2020 by Kitware, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
#    * Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
#    * Neither name of Kitware, Inc. nor the names of any contributors may be used
#    to endorse or promote products derived from this software without specific
#    prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS ``AS IS''
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHORS OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from __future__ import print_function
from __future__ import division

from vital.algo import TrainDetector
from vital.algo import DetectedObjectSetOutput

from vital.types import BoundingBox
from vital.types import CategoryHierarchy
from vital.types import DetectedObjectSet
from vital.types import DetectedObject
from vital.types import DetectedObjectType

from PIL import Image

from distutils.util import strtobool
from shutil import copyfile

import argparse
import numpy as np
import torch
import pickle
import os
import signal
import sys
import subprocess
import threading
import time

class NetHarnTrainer( TrainDetector ):
    """
    Implementation of TrainDetector class
    """
    def __init__( self ):
        TrainDetector.__init__( self )

        self._config_file = "bioharn-det-v14-cascade"
        self._seed_model = ""
        self._train_directory = "deep_training"
        self._output_directory = "category_models"
        self._output_prefix = "custom_cfrnn"
        self._pipeline_template = ""
        self._gpu_count = -1
        self._tmp_training_file = "training_truth.json"
        self._tmp_validation_file = "validation_truth.json"
        self._gt_frames_only = False
        self._chip_width = "640"
        self._chip_overlap = "0.20"
        self._max_epochs = "50"
        self._batch_size = "auto"
        self._timeout = "1209600"
        self._backbone = ""
        self._pipeline_template = ""
        self._categories = []
        self._resize_option = "original_and_resized"
        self._max_scale_wrt_chip = 2.0
        self._no_format = False

    def get_configuration( self ):
        # Inherit from the base class
        cfg = super( TrainDetector, self ).get_configuration()

        cfg.set_value( "config_file", self._config_file )
        cfg.set_value( "seed_model", self._seed_model )
        cfg.set_value( "train_directory", self._train_directory )
        cfg.set_value( "output_directory", self._output_directory )
        cfg.set_value( "output_prefix", self._output_prefix )
        cfg.set_value( "pipeline_template", self._pipeline_template )
        cfg.set_value( "gpu_count", str( self._gpu_count ) )
        cfg.set_value( "gt_frames_only", str( self._gt_frames_only ) )
        cfg.set_value( "chip_width", str( self._chip_width ) )
        cfg.set_value( "chip_overlap", str( self._chip_overlap ) )
        cfg.set_value( "max_epochs", str( self._max_epochs ) )
        cfg.set_value( "batch_size", self._batch_size )
        cfg.set_value( "timeout", self._timeout )
        cfg.set_value( "backbone", self._backbone )
        cfg.set_value( "pipeline_template", self._pipeline_template )
        cfg.set_value( "max_scale_wrt_chip", str( self._max_scale_wrt_chip ) )
        cfg.set_value( "no_format", str( self._no_format ) )

        return cfg

    def set_configuration( self, cfg_in ):
        cfg = self.get_configuration()
        cfg.merge_config( cfg_in )

        # Read configs from file
        self._config_file = str( cfg.get_value( "config_file" ) )
        self._seed_model = str( cfg.get_value( "seed_model" ) )
        self._train_directory = str( cfg.get_value( "train_directory" ) )
        self._output_directory = str( cfg.get_value( "output_directory" ) )
        self._output_prefix = str( cfg.get_value( "output_prefix" ) )
        self._pipeline_template = str( cfg.get_value( "pipeline_template" ) )
        self._gpu_count = int( cfg.get_value( "gpu_count" ) )
        self._gt_frames_only = strtobool( cfg.get_value( "gt_frames_only" ) )
        self._chip_width = str( cfg.get_value( "chip_width" ) )
        self._chip_overlap = str( cfg.get_value( "chip_overlap" ) )
        self._max_epochs = str( cfg.get_value( "max_epochs" ) )
        self._batch_size = str( cfg.get_value( "batch_size" ) )
        self._timeout = str( cfg.get_value( "timeout" ) )
        self._backbone = str( cfg.get_value( "backbone" ) )
        self._pipeline_template = str( cfg.get_value( "pipeline_template" ) )
        self._max_scale_wrt_chip = float( cfg.get_value( "max_scale_wrt_chip" ) )
        self._no_format = strtobool( cfg.get_value( "no_format" ) )

        # Check GPU-related variables
        gpu_memory_available = 0

        if torch.cuda.is_available():
            if self._gpu_count < 0:
                self._gpu_count = torch.cuda.device_count()
            for i in range( self._gpu_count ):
                single_gpu_mem = torch.cuda.get_device_properties( i ).total_memory
                if gpu_memory_available == 0:
                    gpu_memory_available = single_gpu_mem
                else:
                    gpu_memory_available = min( gpu_memory_available, single_gpu_mem )

        if self._batch_size == "auto":
            if gpu_memory_available > 9e9:
                self._batch_size = "4"
            elif gpu_memory_available >= 7e9:
                self._batch_size = "3"
            else:
                self._batch_size = "2"

        # Make required directories and file streams
        if self._train_directory is not None:
            if not os.path.exists( self._train_directory ):
                os.mkdir( self._train_directory )
            self._training_file = os.path.join(
                self._train_directory, self._tmp_training_file )
            self._validation_file = os.path.join(
                self._train_directory, self._tmp_validation_file )
        else:
            self._training_file = self._tmp_training_file
            self._validation_file = self._tmp_validation_file

        if self._output_directory is not None:
            if not os.path.exists( self._output_directory ):
                os.mkdir( self._output_directory )

        from vital.modules.modules import load_known_modules
        load_known_modules()

        if not self._no_format:
            self._training_writer = \
              DetectedObjectSetOutput.create( "coco" )
            self._validation_writer = \
              DetectedObjectSetOutput.create( "coco" )

            self._training_writer.open( self._training_file )
            self._validation_writer.open( self._validation_file )

        # Initialize persistent variables
        self._training_data = []
        self._validation_data = []
        self._sample_count = 0

    def check_configuration( self, cfg ):
        if not cfg.has_value( "config_file" ) or \
          len( cfg.get_value( "config_file") ) == 0:
            print( "A config file must be specified!" )
            return False
        return True

    def filter_truth( self, init_truth, categories ):
        filtered_truth = DetectedObjectSet()
        use_frame = True
        max_length = int( self._max_scale_wrt_chip * float( self._chip_width ) )
        for i, item in enumerate( init_truth ):
            class_lbl = item.type().get_most_likely_class()
            if categories is not None and not categories.has_class_id( class_lbl ):
                continue
            if categories is not None:
                class_lbl = categories.get_class_name( class_lbl )
            elif class_lbl not in self._categories:
                self._categories.append( class_lbl )

            truth_type = DetectedObjectType( class_lbl, 1.0 )
            item.set_type( truth_type )

            if item.bounding_box().width() > max_length or \
               item.bounding_box().height() > max_length:
                use_frame = False
                break

            filtered_truth.add( item )
        return filtered_truth, use_frame

    def add_data_from_disk( self, categories, train_files, train_dets, test_files, test_dets ):
        if self._no_format:
            return
        if len( train_files ) != len( train_dets ):
            print( "Error: train file and groundtruth count mismatch" )
            return
        if categories is not None:
            self._categories = categories.all_class_names()
        for i in range( len( train_files ) + len( test_files ) ):
            if i < len( train_files ):
                filename = train_files[ i ]
                groundtruth, use_frame = self.filter_truth( train_dets[ i ], categories )
                if use_frame:
                    self._training_writer.write_set( groundtruth, os.path.abspath( filename ) )
            else:
                filename = test_files[ i-len( train_files ) ]
                groundtruth, use_frame = self.filter_truth( test_dets[ i-len( train_files ) ], categories )
                if use_frame:
                    self._validation_writer.write_set( groundtruth, os.path.abspath( filename ) )

    def update_model( self ):
        if not self._no_format:
            self._training_writer.complete()
            self._validation_writer.complete()

        gpu_string = ','.join([ str(i) for i in range(0,self._gpu_count) ])

        cmd = [ "python.exe" if os.name == 'nt' else "python",
                "-m",
                "bioharn.detect_fit",
                "--nice=" + self._config_file,
                "--train_dataset=" + self._training_file,
                "--vali_dataset=" + self._validation_file,
                "--workdir=" + self._train_directory,
                "--schedule=ReduceLROnPlateau-p2-c2",
                "--augment=complex",
                "--init=noop",
                "--arch=cascade",
                "--optim=sgd",
                "--lr=1e-3",
                "--max_epoch=" + self._max_epochs,
                "--input_dims=window",
                "--window_dims=" + self._chip_width + "," + self._chip_width,
                "--window_overlap=" + self._chip_overlap,
                "--multiscale=True",
                "--normalize_inputs=True",
                "--workers=4",
                "--sampler_backend=none",
                "--xpu=" + gpu_string,
                "--batch_size=" + self._batch_size,
                "--bstep=4",
                "--timeout=" + self._timeout,
                "--channels=rgb" ]

        if len( self._backbone ) > 0:
            cmd.append( "--backbone_init=" + self._backbone )

        if len( self._seed_model ) > 0:
            cmd.append( "--pretrained=" + self._seed_model )

        if threading.current_thread().__class__.__name__ == '_MainThread':
          signal.signal( signal.SIGINT, lambda signal, frame: self.interupt_handler() )
          signal.signal( signal.SIGTERM, lambda signal, frame: self.interupt_handler() )

        self.proc = subprocess.Popen( cmd )
        self.proc.wait()

        self.save_final_model()

        print( "\nModel training complete!\n" )

    def interupt_handler( self ):
        self.proc.send_signal( signal.SIGINT )
        timeout = 0
        while self.proc.poll() is None:
            time.sleep( 0.1 )
            timeout += 0.1
            if timeout > 5:
                self.proc.kill()
                break
        self.save_final_model()
        sys.exit( 0 )

    def save_final_model( self ):
        if len( self._pipeline_template ) > 0:
            # Copy model file to final directory
            output_model_name = "trained_detector.zip"

            final_model = os.path.join( self._train_directory,
              "fit", "nice", self._config_file, "deploy.zip" )
            output_model = os.path.join( self._output_directory,
              output_model_name )

            if not os.path.exists( final_model ):
                print( "\nModel failed to finsh training\n" )
                sys.exit( 0 )

            copyfile( final_model, output_model )

            # Copy pipeline file
            fin = open( self._pipeline_template )
            fout = open( os.path.join( self._output_directory, "detector.pipe" ), 'w' )
            all_lines = []
            for s in list( fin ):
                all_lines.append( s )
            for i, line in enumerate( all_lines ):
                line = line.replace( "[-MODEL-FILE-]", output_model_name )
                all_lines[i] = line.replace( "[-WINDOW-OPTION-]", self._resize_option )
            for s in all_lines:
                fout.write( s )
            fout.close()
            fin.close()

def __vital_algorithm_register__():
    from vital.algo import algorithm_factory

    # Register Algorithm
    implementation_name = "netharn"

    if algorithm_factory.has_algorithm_impl_name(
      NetHarnTrainer.static_type_name(), implementation_name ):
        return

    algorithm_factory.add_algorithm( implementation_name,
      "PyTorch NetHarn detection training routine", NetHarnTrainer )

    algorithm_factory.mark_algorithm_as_loaded( implementation_name )
