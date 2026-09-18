#-----------------------------------------------------------------------------
set(MODULE_NAME Agent_CLI)
set(FOLDER_LIBRARY Agent_CLI_utils)

set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  ${FOLDER_LIBRARY}/__init__.py
  ${FOLDER_LIBRARY}/utils.py
  ${FOLDER_LIBRARY}/parameter_extraction_improved.py
  ${FOLDER_LIBRARY}/parameter_validator.py
  )

# Agent_CLI est un CLI : `Agent.py` l'appelle par `slicer.modules.agent_cli`.
# Slicer ne le reconnait comme tel que s'il trouve sa description XML a cote du
# script. Elle manquait ici : dans un build installe, le script se retrouvait
# seul, Slicer tentait de le charger comme un module scripte, echouait faute de
# classe widget, et `slicer.modules.agent_cli` n'existait pas. Le defaut ne se
# voit pas en arbre de developpement, ou le .xml est la.
set(MODULE_PYTHON_RESOURCES
  Resources/Icons/${MODULE_NAME}.png
  Resources/UI/${MODULE_NAME}.ui
  ${MODULE_NAME}.xml
  manifest.yaml
  )

SlicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  RESOURCES ${MODULE_PYTHON_RESOURCES}
)
