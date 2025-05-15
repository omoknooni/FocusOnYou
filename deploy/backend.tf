terraform {
    cloud {
        organization = "infra-team"
        workspaces {
            name = "focusonyou"
        }
    }
}