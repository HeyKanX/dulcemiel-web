pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
        timestamps()
    }

    parameters {
        booleanParam(
            name: 'PUBLICAR_RESULTADOS_TESTLINK',
            defaultValue: false,
            description: 'Publica únicamente resultados producidos y validados por esta ejecución.'
        )
    }

    stages {
        stage('Checkout') {
            steps {
                deleteDir()
                checkout scm
            }
        }

        stage('Backend - pruebas Maven') {
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE', message: 'Fallaron las pruebas Maven del backend; se continuará para recopilar los demás resultados.') {
                    script {
                        if (isUnix()) {
                            dir('backend') { sh './mvnw -B -ntp test' }
                        } else {
                            dir('backend') { bat 'mvnw.cmd -B -ntp test' }
                        }
                    }
                }
            }
        }

        stage('Frontend - pruebas unitarias') {
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE', message: 'Fallaron las pruebas unitarias del frontend; se continuará con las etapas restantes.') {
                    script {
                        if (isUnix()) {
                            dir('frontend') {
                                sh 'npm ci'
                                sh 'npm run test:coverage -- --browsers=ChromeHeadless'
                            }
                        } else {
                            dir('frontend') {
                                bat 'npm ci'
                                bat 'npm run test:coverage -- --browsers=ChromeHeadless'
                            }
                        }
                    }
                }
            }
        }

        stage('Frontend - compilación') {
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE', message: 'Falló la compilación del frontend; se continuará con la validación de resultados.') {
                    script {
                        if (isUnix()) {
                            dir('frontend') { sh 'npm run build -- --configuration development' }
                        } else {
                            dir('frontend') { bat 'npm run build -- --configuration development' }
                        }
                    }
                }
            }
        }

        stage('Instalar herramientas de QA') {
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE', message: 'No quedaron listas las dependencias de QA; las suites dependientes se marcarán como omitidas.') {
                    bat 'pwsh -NoProfile -ExecutionPolicy Bypass -File qa\\jenkins\\install-dependencies.ps1'
                }
                script {
                    env.QA_DEPS_READY = fileExists('qa/.local/jenkins-deps-ready.flag') ? 'true' : 'false'
                }
            }
        }

        stage('Preparar stack QA aislado en Docker') {
            when { expression { env.QA_DEPS_READY == 'true' } }
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE', message: 'No se pudo preparar el entorno aislado; las suites funcionales se marcarán como omitidas.') {
                    bat 'pwsh -NoProfile -ExecutionPolicy Bypass -File qa\\jenkins\\prepare-qa.ps1'
                }
                script {
                    env.QA_ENV_READY = fileExists('qa/.local/jenkins-ready.flag') ? 'true' : 'false'
                }
            }
        }

        stage('API - Newman') {
            when { expression { env.QA_ENV_READY == 'true' } }
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE', message: 'Newman encontró fallos; se continuará con las demás suites.') {
                    bat 'pwsh -NoProfile -ExecutionPolicy Bypass -File qa\\jenkins\\run-suite.ps1 -Suite Newman'
                }
            }
        }

        stage('Interfaz - Behave y Selenium') {
            when { expression { env.QA_ENV_READY == 'true' } }
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE', message: 'Behave/Selenium encontró fallos; se continuará con las demás suites.') {
                    bat 'pwsh -NoProfile -ExecutionPolicy Bypass -File qa\\jenkins\\run-suite.ps1 -Suite Behave'
                }
            }
        }

        stage('Compatibilidad - Playwright') {
            when { expression { env.QA_ENV_READY == 'true' } }
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE', message: 'Playwright encontró fallos de compatibilidad; se continuará con las demás suites.') {
                    bat 'pwsh -NoProfile -ExecutionPolicy Bypass -File qa\\jenkins\\run-suite.ps1 -Suite Compatibility'
                }
            }
        }

        stage('Accesibilidad automatizada - axe-core') {
            when { expression { env.QA_ENV_READY == 'true' } }
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE', message: 'axe-core encontró violaciones o errores de navegación; se continuará con las demás suites.') {
                    bat 'pwsh -NoProfile -ExecutionPolicy Bypass -File qa\\jenkins\\run-suite.ps1 -Suite Axe'
                }
            }
        }

        stage('K6 - humo') {
            when { expression { env.QA_ENV_READY == 'true' } }
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE', message: 'Falló el perfil K6 de humo; se continuará con los demás perfiles.') {
                    bat 'pwsh -NoProfile -ExecutionPolicy Bypass -File qa\\jenkins\\run-suite.ps1 -Suite K6Smoke'
                }
            }
        }

        stage('K6 - línea base') {
            when { expression { env.QA_ENV_READY == 'true' } }
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE', message: 'Falló el perfil K6 de línea base; se continuará con los demás perfiles.') {
                    bat 'pwsh -NoProfile -ExecutionPolicy Bypass -File qa\\jenkins\\run-suite.ps1 -Suite K6Baseline'
                }
            }
        }

        stage('K6 - carga moderada') {
            when { expression { env.QA_ENV_READY == 'true' } }
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE', message: 'Falló el perfil K6 moderado; se continuará con los demás perfiles.') {
                    bat 'pwsh -NoProfile -ExecutionPolicy Bypass -File qa\\jenkins\\run-suite.ps1 -Suite K6Moderate'
                }
            }
        }

        stage('K6 - estrés progresivo') {
            when { expression { env.QA_ENV_READY == 'true' } }
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE', message: 'Falló K6 de estrés progresivo; se continuará con los demás perfiles.') {
                    bat 'pwsh -NoProfile -ExecutionPolicy Bypass -File qa\\jenkins\\run-suite.ps1 -Suite K6Stress'
                }
            }
        }

        stage('K6 - pico repentino') {
            when { expression { env.QA_ENV_READY == 'true' } }
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE', message: 'Falló K6 de pico repentino; se continuará con los demás perfiles.') {
                    bat 'pwsh -NoProfile -ExecutionPolicy Bypass -File qa\\jenkins\\run-suite.ps1 -Suite K6Spike'
                }
            }
        }

        stage('K6 - carga sostenida') {
            when { expression { env.QA_ENV_READY == 'true' } }
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE', message: 'Falló K6 de carga sostenida; se continuará con TestLink.') {
                    bat 'pwsh -NoProfile -ExecutionPolicy Bypass -File qa\\jenkins\\run-suite.ps1 -Suite K6Sustained'
                }
            }
        }

        stage('Generar resumen automatizado para TestLink') {
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE', message: 'No se pudo generar el resumen de casos automatizados para TestLink.') {
                    bat 'pwsh -NoProfile -ExecutionPolicy Bypass -File qa\\jenkins\\generate-summary.ps1'
                }
            }
        }

        stage('Validar resumen TestLink') {
            when {
                expression { fileExists('qa/testlink/results/current-run.json') || params.PUBLICAR_RESULTADOS_TESTLINK }
            }
            steps {
                script {
                    if (!fileExists('qa/testlink/results/current-run.json')) {
                        error('No hay resumen de esta corrida; no se publicará nada en TestLink.')
                    }
                    if (isUnix()) {
                        sh 'python3 qa/testlink/publish_results.py --results qa/testlink/results/current-run.json'
                    } else {
                        bat 'py qa\\testlink\\publish_results.py --results qa\\testlink\\results\\current-run.json'
                    }
                    env.TESTLINK_SUMMARY_VALID = 'true'
                }
            }
        }

        stage('Publicar resultados en TestLink') {
            when {
                expression { params.PUBLICAR_RESULTADOS_TESTLINK && env.TESTLINK_SUMMARY_VALID == 'true' }
            }
            steps {
                script {
                    def requiredFiles = [
                        'qa/testlink/publish_results.py',
                        'qa/testlink/results/case-id-map.json',
                        'qa/testlink/results/current-run.json'
                    ]
                    def missingFiles = requiredFiles.findAll { !fileExists(it) }
                    if (!missingFiles.isEmpty()) {
                        error('Publicación cancelada: faltan artefactos de esta ejecución: ' + missingFiles.join(', '))
                    }
                    if (!env.TESTLINK_URL?.trim()) {
                        error('Publicación cancelada: configure TESTLINK_URL en Jenkins.')
                    }
                }

                withCredentials([string(credentialsId: 'testlink-devkey', variable: 'TESTLINK_DEVKEY')]) {
                    script {
                        if (isUnix()) {
                            sh 'python3 qa/testlink/publish_results.py --results qa/testlink/results/current-run.json --publish'
                        } else {
                            bat 'py qa\\testlink\\publish_results.py --results qa\\testlink\\results\\current-run.json --publish'
                        }
                    }
                }
            }
        }
    }

    post {
        always {
            junit testResults: 'backend/target/surefire-reports/TEST-*.xml', allowEmptyResults: true
            junit testResults: 'qa/artifacts/**/*.xml', allowEmptyResults: true
            archiveArtifacts artifacts: 'backend/target/surefire-reports/**,frontend/coverage/**,frontend/dist/**,qa/artifacts/**,qa/testlink/results/current-run.json,qa/testlink/results/publication-report.json', allowEmptyArchive: true
            script {
                if (!isUnix()) {
                    bat 'if exist qa\\.local\\jenkins-run.json pwsh -NoProfile -ExecutionPolicy Bypass -File qa\\jenkins\\cleanup-qa.ps1'
                }
            }
        }
    }
}
