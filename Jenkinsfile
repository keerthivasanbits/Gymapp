pipeline {
    agent any

    environment {
        DISPLAY = ':99'
        PYTHONUNBUFFERED = '1'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scms
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --upgrade pip
                    if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
                    pip install pytest pytest-cov
                '''
            }
        }

        stage('Test Execution') {
            steps {
                sh '''
                    . .venv/bin/activate
                    xvfb-run -a -s "-screen 0 1024x768x24" pytest aceestver_test_1.py -v --junitxml=test-results.xml
                '''
            }
        }
    }

    post {
        always {
            junit allowEmptyResults: true, testResults: 'test-results.xml'
        }
        cleanup {
            sh 'rm -rf .venv test_fitness.db'
        }
    }
}