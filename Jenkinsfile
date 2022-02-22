pipeline{
  agent {label 'main'}
  stages{
    stage('Cleaning WS'){
      steps{
        cleanWs()
      }
    }
    stage('repo pulling'){
      steps{
        git branch: 'main', url: 'https://github.com/saiprasadrapeti/projectrepo.git'
        sh "ls"
      }
    }
    stage('Terraform code exucution'){
      steps{
        sh "aws lambda create-function --function-name my-function --runtime python3.9 --timeout 840 --zip-file fileb://my-function.zip --handler my-function.lambda_handler  --role arn:aws:iam::751765126997:role/sairole --region us-east-2"
      }
    }
    stage('Cleaning WS1'){
      steps{
        cleanWs()
      }
    }
  }
}
