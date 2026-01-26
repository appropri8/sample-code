package kubernetes.podsecurity

test_deny_non_root {
    input := {
        "kind": "Pod",
        "metadata": {"namespace": "default"},
        "spec": {
            "containers": [{
                "name": "app",
                "image": "nginx:latest"
            }]
        }
    }
    deny[msg] with input as input
    msg == "Container 'app' must run as non-root user. Set securityContext.runAsNonRoot: true"
}

test_deny_read_write_filesystem {
    input := {
        "kind": "Pod",
        "metadata": {"namespace": "default"},
        "spec": {
            "containers": [{
                "name": "app",
                "image": "nginx:latest",
                "securityContext": {
                    "runAsNonRoot": true
                }
            }]
        }
    }
    deny[msg] with input as input
    msg == "Container 'app' must use read-only root filesystem. Set securityContext.readOnlyRootFilesystem: true"
}

test_deny_privileged {
    input := {
        "kind": "Pod",
        "metadata": {"namespace": "default"},
        "spec": {
            "containers": [{
                "name": "app",
                "image": "nginx:latest",
                "securityContext": {
                    "runAsNonRoot": true,
                    "readOnlyRootFilesystem": true,
                    "privileged": true
                }
            }]
        }
    }
    deny[msg] with input as input
    msg == "Container 'app' cannot run in privileged mode. Remove securityContext.privileged or set to false"
}

test_allow_compliant_pod {
    input := {
        "kind": "Pod",
        "metadata": {"namespace": "default"},
        "spec": {
            "containers": [{
                "name": "app",
                "image": "nginx:latest",
                "securityContext": {
                    "runAsNonRoot": true,
                    "readOnlyRootFilesystem": true,
                    "allowPrivilegeEscalation": false
                }
            }]
        }
    }
    count(deny) == 0 with input as input
}

test_allow_system_namespace {
    input := {
        "kind": "Pod",
        "metadata": {"namespace": "kube-system"},
        "spec": {
            "containers": [{
                "name": "app",
                "image": "nginx:latest"
            }]
        }
    }
    count(deny) == 0 with input as input
}
