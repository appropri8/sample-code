package kubernetes.images

approved_registries := {
    "gcr.io",
    "docker.io/your-org",
    "quay.io/your-org",
    "registry.example.com"
}

deny[msg] {
    input.kind == "Pod"
    container := input.spec.containers[_]
    image := container.image
    registry := get_registry(image)
    not registry in approved_registries
    msg := sprintf("Container '%s' uses unapproved registry '%s'. Only images from approved registries are allowed.", [container.name, registry])
}

deny[msg] {
    input.kind == "Pod"
    container := input.spec.containers[_]
    image := container.image
    not has_digest(image)
    msg := sprintf("Container '%s' must use image digest instead of tag. Use format: image@sha256:...", [container.name])
}

get_registry(image) := registry {
    parts := split(image, "/")
    count(parts) > 1
    registry := parts[0]
}

get_registry(image) := "docker.io" {
    parts := split(image, "/")
    count(parts) == 1
}

has_digest(image) {
    contains(image, "@sha256:")
}
