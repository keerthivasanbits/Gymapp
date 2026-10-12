pipeline {
    agent any

    environment {
        DISPLAY = ':99'
        PYTHONUNBUFFERED = '1'
    }

    stages {
        stage('Install Dependencies') {
            steps {
                sh '''
                    # Set up an isolated Python virtual environment
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --upgrade pip

                    # Install project requirements
                    if [ -f requirements.txt ]; then
                        pip install -r requirements.txt
                    fi

                    # Ensure testing tools are installed
                    pip install pytest pytest-cov
                '''
            }
        }

        stage('Run Pytest under Xvfb') {
            steps {
                sh '''
                    . .venv/bin/activate

                    # Run tests headlessly using xvfb-run to prevent Tkinter display crashes
                    xvfb-run -a -s "-screen 0 1024x768x24" pytest aceestver_test_1.py \
                        --junitxml=test-results.xml \
                        -v
                '''
            }
        }
    }

    post {
        always {
            // Collect and display test results in Jenkins UI
            junit allowEmptyResults: true, testResults: 'test-results.xml'
        }
        cleanup {
            // Clean up virtual environment and any temporary SQLite databases
            sh 'rm -rf .venv test_fitness.db'
        }
    }
}