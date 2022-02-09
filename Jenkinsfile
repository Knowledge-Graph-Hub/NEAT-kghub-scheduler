pipeline {
    agent {
        docker {
            reuseNode false
            image 'justaddcoffee/ubuntu20-python-3-8-5-dev:8'
        }
    }
    triggers{
        cron('1 9 * * 1')
    }
    environment {
        RUNSTARTDATE = sh(script: "echo `date +%Y%m%d`", returnStdout: true).trim()
        //S3PROJECTDIR = 'kg-idg' // no trailing slash

        //MERGEDKGNAME_BASE = "KG-IDG"
        //MERGEDKGNAME_GENERIC = "merged-kg"
        GCLOUD_PROJECT = 'test-project-covid-19-277821'
        GCLOUD_VM='gpgpgpuwhereareyou'
        GCLOUD_ZONE='us-central1-a'

        NEAT_DIR = '~jtr4v/NEAT'
        NEAT_SCHEDULER_DIR = '~jtr4v/NEAT-kghub-scheduler'
    }

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    stages {
        // Very first: pause for a minute to give a chance to
        // cancel and clean the workspace before use.
        stage('Ready and clean') {
            steps {
                // Give us a minute to cancel if we want.
                sleep time: 30, unit: 'SECONDS'
            }
        }

        stage('Initialize') {
            steps {
                // print some info
                dir('./gitrepo') {
                    sh 'env > env.txt'
                    sh 'echo $BRANCH_NAME > branch.txt'
                    sh 'echo "$BRANCH_NAME"'
                    sh 'cat env.txt'
                    sh 'cat branch.txt'
                    sh "echo $RUNSTARTDATE > dow.txt"
                    sh "echo $RUNSTARTDATE"
                    sh "python3.8 --version"
                    sh "id"
                    sh "whoami" // this should be jenkinsuser
                    // if the above fails, then the docker host didn't start the docker
                    // container as a user that this image knows about. This will
                    // likely cause lots of problems (like trying to write to $HOME
                    // directory that doesn't exist, etc), so we should fail here and
                    // have the user fix this

                }
            }
        }

        stage('Build NEAT-kghub-scheduler') {
            steps {
                dir('./gitrepo') {
                    git(
                            url: 'https://github.com/Knowledge-Graph-Hub/NEAT-kghub-scheduler',
                            branch: env.BRANCH_NAME
                    )
                    sh '/usr/bin/python3.8 -m venv venv'
                    sh '. venv/bin/activate'
                    // Now move on to the actual install + reqs
                    //sh './venv/bin/pip install .'
                    sh './venv/bin/pip install git+https://github.com/Knowledge-Graph-Hub/NEAT.git'
                }
            }
        }

        stage('Spin up Gcloud instance') {
            when { anyOf { branch 'main' } }
            steps {
                dir('./gcloud') {
                    withCredentials([file(credentialsId: 'GCLOUD_CRED_JSON', variable: 'GCLOUD_CRED_JSON')]) {
                        echo 'Trying to start up instance...'
                            // keep trying to start the instance until success
                            //
                            sh '''#!/bin/bash
                                  gcloud auth activate-service-account --key-file=$GCLOUD_CRED_JSON --project $GCLOUD_PROJECT
                                  STATUS=$(gcloud compute instances describe $GCLOUD_VM --zone=$GCLOUD_ZONE --format="yaml(status)")
                                  n=0
                                  until [ "$n" -ge 100 ]
                                  do
                                       echo "instance $GCLOUD_VM $STATUS; trying to start instance..."
                                       gcloud compute instances start $GCLOUD_VM --zone=$GCLOUD_ZONE
                                       STATUS=$(gcloud compute instances describe $GCLOUD_VM --zone=$GCLOUD_ZONE --format="yaml(status)")
                                       [ "$STATUS" != "status: TERMINATED" ] && break
                                       n=$((n+1))
                                       echo "no dice - sleeping for 30 s"
                                       sleep 30
                                  done
                                  if [ "$STATUS" == "status: TERMINATED" ]
                                  then
                                        echo ERROR: Failed to start instance
                                        exit 1
                                  else
                                        echo started instance
                                  fi
                                  gcloud compute instances describe $GCLOUD_VM --zone=$GCLOUD_ZONE --format="yaml(status)"
                                  gcloud auth list --filter=status:ACTIVE --format="value(account)"
                                  gcloud compute os-login describe-profile
                            '''
                    }
                }

            }
        }
        stage('Update dependencies on Gcloud instance') {
            when { anyOf { branch 'main' } }
            steps {
                dir('./gcloud') {
                    withCredentials([file(credentialsId: 'GCLOUD_CRED_JSON', variable: 'GCLOUD_CRED_JSON')]) {
                        echo 'Performing dependency update on Gcloud instance...'
                        script {
                            def EXIT_CODE_NEAT_SETUP=sh script:"gcloud compute ssh $GCLOUD_VM --zone $GCLOUD_ZONE --ssh-flag=\"-tt\" --command=\" cd $NEAT_DIR && git pull && pip install . && cd .. \"", returnStatus:true
                            def EXIT_CODE_NEATSCHED_SETUP=sh script:"gcloud compute ssh $GCLOUD_VM --zone $GCLOUD_ZONE --ssh-flag=\"-tt\" --command=\" cd $NEAT_SCHEDULER_DIR && git pull && pip install . && cd .. \"", returnStatus:true
                            if(EXIT_CODE_NEAT_SETUP != 0){
                                echo 'Failed while updating NEAT...'
                                currentBuild.result = 'FAILED'
                                return
                            }
                            if(EXIT_CODE_NEATSCHED_SETUP != 0){
                                echo 'Failed while updating NEAT-kghub-scheduler...'
                                currentBuild.result = 'FAILED'
                                return
                            }
                        }
                    }
                }

            }
        }
        stage('Check for new NEAT projects and run') {
            when { anyOf { branch 'main' } }
            steps {
                dir('./gcloud') {
                    withCredentials([file(credentialsId: 'GCLOUD_CRED_JSON', variable: 'GCLOUD_CRED_JSON')]) {
                        echo 'Checking for new NEAT configs on KG-Hub...'
                        script {
                            // Use the scheduler to check the KG-Hub bucket
                            def EXIT_CODE_NEAT_CHECK=sh script:"gcloud compute ssh $GCLOUD_VM --zone $GCLOUD_ZONE --ssh-flag=\"-tt\" --command=\" cd $NEAT_SCHEDULER_DIR && python check.py --bucket kg-hub-public-data && cd ..  \"", returnStatus:true
                            if(EXIT_CODE_NEAT_CHECK != 0){
                                echo 'Failed while checking for NEAT configs...'
                                currentBuild.result = 'FAILED'
                                return
                            }
                            // Run any new configs - they will be on the current directory (before cd to NEAT)
                            // This shouldn't do anything if there are no new configs
                            def EXIT_CODE_NEAT_RUN=sh script:"gcloud compute ssh $GCLOUD_VM --zone $GCLOUD_ZONE --ssh-flag=\"-tt\" --command=\" cd $NEAT_SCHEDULER_DIR && sh run_neat.sh && cd ..  \"", returnStatus:true
                            if(EXIT_CODE_NEAT_RUN != 0){
                                echo 'Failed while in a NEAT run...'
                                currentBuild.result = 'FAILED'
                                return
                            }
                            // TODO: ensure the results get placed in the right location
                            // TODO: if this is the most recent build, copy graph_ml to the 'current' directory too

                            // clean up
                            sh 'rm neat*.y*'
                        }
                    }
                }

            }
        }          
    }

    post {
        always {
            echo 'In always'
            echo 'Shut down gcloud instance'
            dir('./gcloud') {
                withCredentials([file(credentialsId: 'GCLOUD_CRED_JSON', variable: 'GCLOUD_CRED_JSON')]) {
                    echo 'Trying to stop instance...'
                        // keep trying to stop the instance until success
                        sh '''#!/bin/bash
                              gcloud auth activate-service-account --key-file=$GCLOUD_CRED_JSON --project $GCLOUD_PROJECT
                              STATUS=$(gcloud compute instances describe $GCLOUD_VM --zone=$GCLOUD_ZONE --format="yaml(status)")
                              while true
                              do
                                   echo "instance $GCLOUD_VM $STATUS; trying to stop instance..."
                                   gcloud compute instances stop $GCLOUD_VM --zone=$GCLOUD_ZONE
                                   STATUS=$(gcloud compute instances describe $GCLOUD_VM --zone=$GCLOUD_ZONE --format="yaml(status)")
                                   [ "$STATUS" == "status: TERMINATED" ] && break
                                   echo "no dice - sleeping for 10 s"
                                   sleep 10
                              done
                              gcloud compute instances describe $GCLOUD_VM --zone=$GCLOUD_ZONE --format="yaml(status)"
                        '''
                }
            }

            echo 'Cleaning workspace...'
            cleanWs()
        }
        success {
            echo 'I succeeded!'
        }
        unstable {
            echo 'I am unstable :/'
        }
        failure {
            echo 'I failed :('
        }
        changed {
            echo 'Things were different before...'
        }
    }
}