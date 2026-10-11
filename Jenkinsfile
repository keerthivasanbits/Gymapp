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
                echo 'Installing python dependencies'
                sh '''
                    python3 -m venv .venv
                    .venv/bin/pip install --upgrade pip
                    .venv/bin/pip install -r requirements.txt
                '''
            }
        }

        stage('Test') {
            steps {
                echo 'Running Automated Test with Virtual Display'
                sh '''
                    # -a automatically finds an available display number and cleans up on exit
                    xvfb-run -a .venv/bin/pytest aceestver_test_1.py
                '''
            }
        }
    }
}