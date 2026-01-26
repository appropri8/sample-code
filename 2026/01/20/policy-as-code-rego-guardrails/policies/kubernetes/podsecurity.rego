package kubernetes.podsecurity

deny[msg] {
    input.kind == "Pod"
    container := input.spec.containers[_]
    not container.securityContext.runAsNonRoot
    msg := sprintf("Container '%s' must run as non-root user. Set securityContext.runAsNonRoot: true", [container.name])
}

deny[msg] {
    input.kind == "Pod"
    container := input.spec.containers[_]
    not container.securityContext.readOnlyRootFilesystem
    msg := sprintf("Container '%s' must use read-only root filesystem. Set securityContext.readOnlyRootFilesystem: true", [container.name])
}

deny[msg] {
    input.kind == "Pod"
    container := input.spec.containers[_]
    container.securityContext.privileged == true
    msg := sprintf("Container '%s' cannot run in privileged mode. Remove securityContext.privileged or set to false", [container.name])
}

deny[msg] {
    input.kind == "Pod"
    container := input.spec.containers[_]
    not container.securityContext.allowPrivilegeEscalation == false
    msg := sprintf("Container '%s' must disable privilege escalation. Set securityContext.allowPrivilegeEscalation: false", [container.name])
}

# Allow exception for system namespaces
allow {
    input.metadata.namespace == "kube-system"
}

allow {
    input.metadata.namespace == "kube-public"
}
