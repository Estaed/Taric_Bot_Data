@echo off
echo Running all Taric Bot AI tests...
echo.

echo Running Combat Metrics Tests...
python test_combat_metrics.py

echo.
echo Running Feature Extraction Tests...
python test_feature_extraction.py

echo.
echo Running Enhanced Data Tests...
python test_enhanced_data.py

echo.
echo Running File Organization Tests...
python test_file_organization.py

echo.
echo Running Check State File Tests...
python check_state_file.py

echo.
echo Running Action Analysis Tests...
python analyze_actions.py

echo.
echo Running Single Match Processing Tests...
python process_single_match.py

echo.
echo All tests completed. 