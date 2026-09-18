#-----------------------------------------------------------------------------
set(MODULE_NAME BATCHDENTALSEG)

#-----------------------------------------------------------------------------
set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  BATCHDENTALSEGLib/__init__.py
  BATCHDENTALSEGLib/IconPath.py
  BATCHDENTALSEGLib/PythonDependencyChecker.py
  BATCHDENTALSEGLib/Queue.py
  BATCHDENTALSEGLib/SegmentationWidget.py
  BATCHDENTALSEGLib/Signal.py
  BATCHDENTALSEGLib/Utils.py
  Testing/__init__.py
  Testing/IntegrationTestCase.py
  Testing/SegmentationWidgetTestCase.py
  Testing/Utils.py
)

set(MODULE_PYTHON_RESOURCES
  Resources/Icons/DentalSegmentator.png
  Resources/Icons/DentalSegmentator_full_icon.png
  Resources/Icons/DentalSegmentator_full_icon_2.png
  Resources/Icons/info.png
  Resources/Icons/loading.gif
  Resources/Icons/start_icon.png

  # `nnUnetFolder()` et `_modelBasePath()` resolvent tous deux vers
  # Resources/ML : c'est le dossier de modeles livre avec le module, pas un
  # dossier de travail. Sans ces trois fichiers, une install compilee n'y
  # trouve aucun `dataset.json` et le modele ne peut pas etre configure.
  Resources/ML/download_info.json
  Resources/ML/Dataset111_453CT/nnUNetTrainer__nnUNetPlans__3d_fullres/dataset.json
  Resources/ML/Dataset111_453CT/nnUNetTrainer__nnUNetPlans__3d_fullres/plans.json
)

#-----------------------------------------------------------------------------
slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  RESOURCES ${MODULE_PYTHON_RESOURCES}
)
#-----------------------------------------------------------------
