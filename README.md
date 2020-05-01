# Build Status Notifier

Bot for notifying developer in Slack about build execution status in Drone CI, Travis CI or Jenkins.

Guide each build from pushing it to remote till its fully deployment.

It is planned as fully automated solution out-of-the-box. The only thing developer should provide, is proper `config.json` file.

### config.json example

```JSON
{
    "slack": {
        "token": "slack_bot_token_unique_for_each_workspace",
        "bot_direct_messages_id": "channel_id"
    },
    "travis": {
        "token": "travis_api_token"
    }
}
```