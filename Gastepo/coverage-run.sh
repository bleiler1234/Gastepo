#!/usr/bin/env bash
# Description: Code Coverage Analysis With SonarQube
# Developer: yuzhonghua
# Date: 2020-09-25 11:20

echo "[Initial]: Now erase code coverage history..."
coverage erase
echo "[Success]: code coverage history has been erased successfully!"
echo "[Collect]: Now begin collect code coverage..."
coverage run --branch -a --include=Core/**/*.py UnitTest.py
echo "[Success]: code coverage has been collected successfully!"
echo "[Simple Report]: Now display code coverage simple report..."
coverage report -i --include=Core/**/*.py
echo "[Success]: Please review code coverage simple report above."
echo "[Html Report]: Now generate code coverage html report..."
coverage html -i --title=Gastepo -d Output/Coverage/report
echo "[Success]: Please review code coverage html report above."
echo "[Xml Report]: Now generate code coverage xml report file..."
coverage xml -i -o Output/Coverage/coverage.xml
echo "[Success]: code coverage xml report file has been generated successfully!"
echo "[Analysis]: Now begin sonar-scanner analysis..."
sonar-scanner
echo "[Done]: sonar-scanner analysis done, Please review related information on SonarQube web platform!"