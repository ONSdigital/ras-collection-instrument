pipeline {
    agent any

    triggers {
        pollSCM('* * * * *')
    }

    stages {

        stage('dev') {
            agent {
                docker {
                    image 'governmentpaas/cf-cli'
                    args '-u root'
                }
            }

            environment {
                CLOUDFOUNDRY_API = credentials('CLOUDFOUNDRY_API')
                CF_DOMAIN = credentials('CF_DOMAIN')
                DEV_SECURITY = credentials('DEV_SECURITY')
                CF_USER = credentials('CF_USER')
            }
            steps {
                sh "cf login -a https://${env.CLOUDFOUNDRY_API} --skip-ssl-validation -u ${CF_USER_USR} -p ${CF_USER_PSW} -o rmras -s dev"
                sh 'cf push --no-start ras-collection-instrument-dev'
                sh 'cf set-env ras-collection-instrument-dev ONS_ENV dev'
                sh 'cf set-env ras-collection-instrument-dev RABBITMQ_AMQP CHANGEME'
                sh "cf set-env ras-collection-instrument-dev SECURITY_USER_NAME ${env.DEV_SECURITY_USR}"
                sh "cf set-env ras-collection-instrument-dev SECURITY_USER_PASSWORD ${env.DEV_SECURITY_PSW}"

                sh "cf set-env ras-collection-instrument-dev CASE_SERVICE_PROTOCOL https"
                sh "cf set-env ras-collection-instrument-dev CASE_SERVICE_HOST casesvc-dev.${env.CF_DOMAIN}"
                sh "cf set-env ras-collection-instrument-dev CASE_SERVICE_PORT 80"

                sh "cf set-env ras-collection-instrument-dev COLLECTION_EXERCISE_PROTOCOL https"
                sh "cf set-env ras-collection-instrument-dev COLLECTION_EXERCISE_HOST collectionexercisesvc-dev.${env.CF_DOMAIN}"
                sh "cf set-env ras-collection-instrument-dev COLLECTION_EXERCISE_PORT 80"

                sh "cf set-env ras-collection-instrument-dev RM_SURVEY_SERVICE_PROTOCOL https"
                sh "cf set-env ras-collection-instrument-dev RM_SURVEY_SERVICE_HOST surveysvc-dev.${env.CF_DOMAIN}"
                sh "cf set-env ras-collection-instrument-dev RM_SURVEY_SERVICE_PORT 80"
                sh 'cf start ras-collection-instrument-dev'
            }
        }

        stage('ci?') {
            agent none
            steps {
                script {
                    try {
                        timeout(time: 60, unit: 'SECONDS') {
                            script {
                                env.deploy_ci = input message: 'Deploy to CI?', id: 'deploy_ci', parameters: [choice(name: 'Deploy to CI', choices: 'no\nyes', description: 'Choose "yes" if you want to deploy to CI')]
                            }
                        }
                    } catch (ignored) {
                        echo 'Skipping ci deployment'
                    }
                }
            }
        }

        stage('ci') {
            agent {
                docker {
                    image 'governmentpaas/cf-cli'
                    args '-u root'
                }

            }
            when {
                environment name: 'deploy_ci', value: 'yes'
            }

            environment {
                CLOUDFOUNDRY_API = credentials('CLOUDFOUNDRY_API')
                CF_DOMAIN = credentials('CF_DOMAIN')
                CI_SECURITY = credentials('CI_SECURITY')
                CF_USER = credentials('CF_USER')
            }
            steps {
                sh "cf login -a https://${env.CLOUDFOUNDRY_API} --skip-ssl-validation -u ${CF_USER_USR} -p ${CF_USER_PSW} -o rmras -s ci"
                sh 'cf push --no-start ras-collection-instrument-ci'
                sh 'cf set-env ras-collection-instrument-ci ONS_ENV ci'
                sh 'cf set-env ras-collection-instrument-ci RABBITMQ_AMQP CHANGEME'
                sh "cf set-env ras-collection-instrument-ci SECURITY_USER_NAME ${env.CI_SECURITY_USR}"
                sh "cf set-env ras-collection-instrument-ci SECURITY_USER_PASSWORD ${env.CI_SECURITY_PSW}"

                sh "cf set-env ras-collection-instrument-ci CASE_SERVICE_PROTOCOL https"
                sh "cf set-env ras-collection-instrument-ci CASE_SERVICE_HOST casesvc-ci.${env.CF_DOMAIN}"
                sh "cf set-env ras-collection-instrument-ci CASE_SERVICE_PORT 80"

                sh "cf set-env ras-collection-instrument-ci COLLECTION_EXERCISE_PROTOCOL https"
                sh "cf set-env ras-collection-instrument-ci COLLECTION_EXERCISE_HOST collectionexercisesvc-ci.${env.CF_DOMAIN}"
                sh "cf set-env ras-collection-instrument-ci COLLECTION_EXERCISE_PORT 80"

                sh "cf set-env ras-collection-instrument-ci RM_SURVEY_SERVICE_PROTOCOL https"
                sh "cf set-env ras-collection-instrument-ci RM_SURVEY_SERVICE_HOST surveysvc-ci.${env.CF_DOMAIN}"
                sh "cf set-env ras-collection-instrument-ci RM_SURVEY_SERVICE_PORT 80"
                sh 'cf start ras-collection-instrument-ci'
            }
        }

        stage('test?') {
            agent none
            steps {
                script {
                    try {
                        timeout(time: 60, unit: 'SECONDS') {
                            script {
                                env.deploy_test = input message: 'Deploy to test?', id: 'deploy_test', parameters: [choice(name: 'Deploy to test', choices: 'no\nyes', description: 'Choose "yes" if you want to deploy to test')]
                            }
                        }
                    } catch (ignored) {
                        echo 'Skipping test deployment'
                    }
                }
            }
        }

        stage('test') {
            agent {
                docker {
                    image 'governmentpaas/cf-cli'
                    args '-u root'
                }

            }
            when {
                environment name: 'deploy_test', value: 'yes'
            }

            environment {
                CLOUDFOUNDRY_API = credentials('CLOUDFOUNDRY_API')
                CF_DOMAIN = credentials('CF_DOMAIN')
                TEST_SECURITY = credentials('TEST_SECURITY')
                CF_USER = credentials('CF_USER')
            }
            steps {
                sh "cf login -a https://${env.CLOUDFOUNDRY_API} --skip-ssl-validation -u ${CF_USER_USR} -p ${CF_USER_PSW} -o rmras -s test"
                sh 'cf push --no-start ras-collection-instrument-test'
                sh 'cf set-env ras-collection-instrument-test ONS_ENV test'
                sh 'cf set-env ras-collection-instrument-test RABBITMQ_AMQP CHANGEME'
                sh "cf set-env ras-collection-instrument-test SECURITY_USER_NAME ${env.TEST_SECURITY_USR}"
                sh "cf set-env ras-collection-instrument-test SECURITY_USER_PASSWORD ${env.TEST_SECURITY_PSW}"

                sh "cf set-env ras-collection-instrument-test CASE_SERVICE_PROTOCOL https"
                sh "cf set-env ras-collection-instrument-test CASE_SERVICE_HOST casesvc-test.${env.CF_DOMAIN}"
                sh "cf set-env ras-collection-instrument-test CASE_SERVICE_PORT 80"

                sh "cf set-env ras-collection-instrument-test COLLECTION_EXERCISE_PROTOCOL https"
                sh "cf set-env ras-collection-instrument-test COLLECTION_EXERCISE_HOST collectionexertestsesvc-test.${env.CF_DOMAIN}"
                sh "cf set-env ras-collection-instrument-test COLLECTION_EXERCISE_PORT 80"

                sh "cf set-env ras-collection-instrument-test RM_SURVEY_SERVICE_PROTOCOL https"
                sh "cf set-env ras-collection-instrument-test RM_SURVEY_SERVICE_HOST surveysvc-test.${env.CF_DOMAIN}"
                sh "cf set-env ras-collection-instrument-test RM_SURVEY_SERVICE_PORT 80"
                sh 'cf start ras-collection-instrument-test'
            }
        }
    }

    post {
        always {
            cleanWs()
            dir('${env.WORKSPACE}@tmp') {
                deleteDir()
            }
            dir('${env.WORKSPACE}@script') {
                deleteDir()
            }
            dir('${env.WORKSPACE}@script@tmp') {
                deleteDir()
            }
        }
    }
}