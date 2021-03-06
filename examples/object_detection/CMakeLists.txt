###
# Application level pipelines
##

set( EXAMPLE_INSTALL_FILES
     input_image_list_habcam.txt
     input_image_list_small_set.txt )

if( WIN32 )
  set( EXAMPLE_INSTALL_FILES
       ${EXAMPLE_INSTALL_FILES}
       run_default.bat
       run_generic.bat )
else()
  set( EXAMPLE_INSTALL_FILES
       ${EXAMPLE_INSTALL_FILES}
       run_default.sh
       run_generic.sh )
endif()

if( VIAME_DOWNLOAD_MODELS-HABCAM AND VIAME_ENABLE_YOLO )
  if( WIN32 )
    set( EXAMPLE_INSTALL_FILES
         ${EXAMPLE_INSTALL_FILES}
         run_scallop_and_fish.bat
         run_scallop_and_fish_left.bat )
  else()
    set( EXAMPLE_INSTALL_FILES
         ${EXAMPLE_INSTALL_FILES}
         run_scallop_and_fish.sh
         run_scallop_and_fish_left.sh )
  endif()
endif()

if( VIAME_DOWNLOAD_MODELS-HABCAM AND VIAME_ENABLE_PYTORCH-NETHARN )
  if( WIN32 )
    set( EXAMPLE_INSTALL_FILES
         ${EXAMPLE_INSTALL_FILES}
         run_scallop_netharn.bat
         run_scallop_netharn_left.bat )
  else()
    set( EXAMPLE_INSTALL_FILES
         ${EXAMPLE_INSTALL_FILES}
         run_scallop_netharn.sh
         run_scallop_netharn_left.sh )
  endif()
endif()

if( VIAME_DOWNLOAD_MODELS-HABCAM AND VIAME_ENABLE_SCALLOP_TK )
  if( WIN32 )
    set( EXAMPLE_INSTALL_FILES
         ${EXAMPLE_INSTALL_FILES}
         run_scallop_tk.bat
         run_scallop_tk_left.bat )
  else()
    set( EXAMPLE_INSTALL_FILES
         ${EXAMPLE_INSTALL_FILES}
         run_scallop_tk.sh
         run_scallop_tk_left.sh )
  endif()
endif()

if( VIAME_ENABLE_MATLAB )
  if( WIN32 )
    set( EXAMPLE_INSTALL_FILES
         ${EXAMPLE_INSTALL_FILES}
         run_scallop_lanl.bat )
  else()
    set( EXAMPLE_INSTALL_FILES
         ${EXAMPLE_INSTALL_FILES}
         run_scallop_lanl.sh )
  endif()
endif()

if( VIAME_DOWNLOAD_MODELS-ARCTIC-SEAL )

  set( EXAMPLE_INSTALL_FILES
       ${EXAMPLE_INSTALL_FILES}
       input_image_list_seal_eo.txt
       input_image_list_seal_ir.txt )

  if( VIAME_ENABLE_TENSORFLOW )
    if( WIN32 )
      set( EXAMPLE_INSTALL_FILES
           ${EXAMPLE_INSTALL_FILES}
           run_arctic_seal_eo_tf.bat
           run_arctic_seal_ir_tf.bat )
    else()
      set( EXAMPLE_INSTALL_FILES
           ${EXAMPLE_INSTALL_FILES}
           run_arctic_seal_eo_tf.sh
           run_arctic_seal_ir_tf.sh )
    endif()
  endif()

  if( VIAME_ENABLE_YOLO )
    if( WIN32 )
      set( EXAMPLE_INSTALL_FILES
           ${EXAMPLE_INSTALL_FILES}
           run_arctic_seal_fusion_yolo.bat
           run_arctic_seal_eo_yolo.bat
           run_arctic_seal_ir_yolo.bat )
    else()
      set( EXAMPLE_INSTALL_FILES
           ${EXAMPLE_INSTALL_FILES}
           run_arctic_seal_fusion_yolo.sh
           run_arctic_seal_eo_yolo.sh
           run_arctic_seal_ir_yolo.sh )
    endif()
  endif()
endif()

###
# Install pipelines to example directory
##
install( FILES       ${EXAMPLE_INSTALL_FILES}
         DESTINATION examples/object_detection )
