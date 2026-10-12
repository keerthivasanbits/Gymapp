pipeline {
    agent any

    environment {
        // Run tests headlessly using Xvfb
        DISPLAY = ':99'
        PYTHONUNBUFFERED = '1'
    }

    stages {
        stage('Install System Packages') {
            steps {
                sh '''
                    # Ensure Xvfb and Tkinter system libraries are installed on the Jenkins host
                    if command -v apt-get >/dev/null 2>&1; then
                        which xvfb-run >/dev/null 2>&1 || (sudo apt-get update && sudo apt-get install -y xvfb python3-tk)
                    elif command -v dnf >/dev/null 2>&1; then
                        which xvfb-run >/dev/null 2>&1 || (sudo dnf install -y xorg-x11-server-Xvfb python3-tkinter)
                    fi
                '''
            }
        }

        stage('Set Up Virtualenv & Dependencies') {
            steps {
                sh '''
                    # Clean up old virtual environment if corrupted
                    rm -rf .venv

                    # Create fresh virtual environment
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --upgrade pip

                    # Project dependencies required by aceestver_gymapp.py
                    pip install matplotlib fpdf2 pytest pytest-cov

                    # Install requirements.txt if present
                    if [ -f requirements.txt ]; then
                        pip install -r requirements.txt
                    fi
                '''
            }
        }

        stage('Execute Pytest') {
            steps {
                sh '''
                    . .venv/bin/activate

                    # Run tests headlessly through xvfb-run to provide virtual screen for Tkinter
                    xvfb-run -a -s "-screen 0 1024x768x24" pytest \
                        --junitxml=test-results.xml \
                        -v
                '''
            }
        }
    }

    post {
        always {
            // Publish test metrics inside Jenkins build dashboard
            junit allowEmptyResults: true, testResults: 'test-results.xml'
        }
        cleanup {
            // Remove test artifacts and test SQLite databases
            sh 'rm -rf .venv test_fitness.db aceest_fitness.db'
        }
        failure {
            echo 'Build or tests failed. Inspect console output and test-results.xml.'
        }
    }
}