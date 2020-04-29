"""Set of message block templates for Slack."""

# ! Do not add template for merge commit
COMMON_BLOCKS = [
    {
        'type': 'section',
        'text': {
            'type': 'mrkdwn',
            'text': ':heavy_check_mark: :x: Feature branch check has passed',
            # 'text': ':heavy_check_mark: :x: Feature branch check has passed',
        }
    },
    {
        'type': 'section',
        'text': {
            'type': 'mrkdwn',
            'text': '*Branch:*\n {branch} \n*Commit:*\n {commit} \n*Duration:*\n {duration} \n'
        },
        'accessory': {
            'type': 'image',
            'image_url': 'https://travis-ci.com/images/logos/TravisCI-Mascot-1.png',
            'alt_text': 'Travis CI'
        }
    },
    {
        'type': 'actions',
        'elements': [
            {
                'type': 'button',
                'text': {
                    'type': 'plain_text',
                    'text': 'Go to Commit'
                },
                'style': 'danger',
                'url': 'sample link'
                # 'url': 'https://travis-ci.com/github/nifadyev/cubic-spline-interpolator/jobs/320766424'
            },
            {
                'type': 'button',
                'text': {
                    'type': 'plain_text',
                    'text': 'Go to Failed Job'
                    # 'text': 'Go to Pull Request'
                },
                'style': 'danger',
                'value': 'click_me_123'
                # 'url': 'https://travis-ci.com/github/nifadyev/cubic-spline-interpolator/jobs/320766424'
            }
        ]
    }
]

BRANCH_SUCCESS_BLOCKS = [
    {
        'type': 'section',
        'text': {
            'type': 'mrkdwn',
            'text': ':heavy_check_mark: Feature branch check has passed',
        }
    },
    {
        'type': 'section',
        'text': {
            'type': 'mrkdwn',
            'text': None
        },
        'accessory': {
            'type': 'image',
            'image_url': 'https://travis-ci.com/images/logos/TravisCI-Mascot-1.png',
            'alt_text': 'Travis CI'
        }
    },
    {
        'type': 'actions',
        'elements': [
            {
                'type': 'button',
                'text': {
                    'type': 'plain_text',
                    'text': 'Go to Commit'
                },
                'style': 'danger',
                'url': None
            },
            {
                'type': 'button',
                'text': {
                    'type': 'plain_text',
                    'text': 'Go to Pull Request'
                },
                'style': 'danger',
                'value': 'click_me_123',
                'url': None
            }
        ]
    }
]

BRANCH_FAIL_BLOCKS = [
    {
        'type': 'section',
        'text': {
            'type': 'mrkdwn',
            'text': ':x: Feature branch check has failed',
        }
    },
    {
        'type': 'section',
        'text': {
            'type': 'mrkdwn',
            'text': None
        },
        'accessory': {
            'type': 'image',
            'image_url': 'https://travis-ci.com/images/logos/TravisCI-Mascot-1.png',
            'alt_text': 'Travis CI'
        }
    },
    {
        'type': 'actions',
        'elements': [
            {
                'type': 'button',
                'text': {
                    'type': 'plain_text',
                    'text': 'Go to Commit'
                },
                'style': 'danger',
                'url': None
            },
            {
                'type': 'button',
                'text': {
                    'type': 'plain_text',
                    'text': 'Go to Failed Job'
                },
                'style': 'danger',
                'value': 'click_me_123',
                'url': None
            }
        ]
    }
]
