module.exports = {
    "env": {
        "browser": true
    },
    "overrides": [
        {
            "env": {
                "node": true
            },
            "files": [
                ".eslintrc.{js,cjs}"
            ],
            "parserOptions": {
                "sourceType": "script"
            }
        },
        {
            "files": [
                "htdocs/static/vendor/marked.min.js"
            ],
            "parserOptions": {
                "ecmaVersion": 2022
            }
        }
    ],
    "parserOptions": {
        "ecmaVersion": 2018
    },
    "rules": {
    }
}
