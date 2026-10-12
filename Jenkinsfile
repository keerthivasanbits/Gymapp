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
                      .venv/bin/pip install --no-cache-dir -r requirements.txt
                      .venv/bin/pip install pytest pytest-xvfb matplotlib
                      
                      # Start Xvfb manually in the background on display :99
                      Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &
                      
                      # Export the DISPLAY variable so tkinter can find it
                      export DISPLAY=:99
                      
                      # Run your pytest command
                      .venv/bin/pytest aceestver_test_1.py
                '''
            }
        }
    }
}