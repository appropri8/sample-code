package terraform.iam

test_deny_wildcard_action {
    input := {
        "resource_changes": [{
            "type": "aws_iam_role_policy",
            "address": "aws_iam_role_policy.example",
            "change": {
                "after": {
                    "policy": json.marshal({
                        "Statement": [{
                            "Action": "*",
                            "Resource": "*"
                        }]
                    })
                }
            }
        }]
    }
    deny[msg] with input as input
    msg == "IAM policy 'aws_iam_role_policy.example' uses wildcard action '*'. Use specific actions instead."
}

test_deny_wildcard_resource {
    input := {
        "resource_changes": [{
            "type": "aws_iam_role_policy",
            "address": "aws_iam_role_policy.example",
            "change": {
                "after": {
                    "policy": json.marshal({
                        "Statement": [{
                            "Action": "s3:GetObject",
                            "Resource": "*"
                        }]
                    })
                }
            }
        }]
    }
    deny[msg] with input as input
    msg == "IAM policy 'aws_iam_role_policy.example' uses wildcard resource '*'. Use specific resource ARNs instead."
}

test_deny_broad_service_permission {
    input := {
        "resource_changes": [{
            "type": "aws_iam_role_policy",
            "address": "aws_iam_role_policy.example",
            "change": {
                "after": {
                    "policy": json.marshal({
                        "Statement": [{
                            "Action": "s3:*",
                            "Resource": "arn:aws:s3:::my-bucket/*"
                        }]
                    })
                }
            }
        }]
    }
    deny[msg] with input as input
    msg == "IAM policy 'aws_iam_role_policy.example' grants s3:* permissions. Use specific S3 actions (e.g., s3:GetObject, s3:PutObject)."
}

test_allow_specific_actions {
    input := {
        "resource_changes": [{
            "type": "aws_iam_role_policy",
            "address": "aws_iam_role_policy.example",
            "change": {
                "after": {
                    "policy": json.marshal({
                        "Statement": [{
                            "Action": ["s3:GetObject", "s3:PutObject"],
                            "Resource": "arn:aws:s3:::my-bucket/*"
                        }]
                    })
                }
            }
        }]
    }
    count(deny) == 0 with input as input
}
