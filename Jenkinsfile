pipeline {
    agent any
    triggers {
        githubPush()
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out main branch'
                checkout scm
            }
        }

        stage('Build') {
            steps {
                echo 'Installing Python dependencies'
                sh '''
                    python3 -m venv .venv
                    .venv/bin/pip install --no-cache-dir -r requirements.txt
                '''
            }
        }

        stage('Test') {
            steps {
                echo 'Running Automated Tests with xvfb'
                sh '''
                    python3 -m venv .venv
                    .venv/bin/pip install --no-cache-dir -r requirements.txt
                    .venv/bin/pip install pytest pytest-xvfb matplotlib
                    xvfb-run -a .venv/bin/pytest --xvfb aceestver_test_1.py
                '''
            }
        }
    }
}
