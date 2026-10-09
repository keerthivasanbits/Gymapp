pipeline {
    agent any
    triggers{
      githubPush()
    }

    stages{
        stage('Checkout'){
            steps{
                echo 'Checking out main branch'
                checkout scm
            }
        }

        stage('Build'){
            steps{
                echo 'installing python dependencies'

                sh '''
                     python3 -m venv .venv
                     .venv/bin/pip install -r requirements.txt
                '''
            }
        }

        stage('Test'){
            steps{
                echo 'Running Automated Test'

                sh '''
                    .venv/bin/pytest aceest_app.py
                '''
            }
        }
    }
}
