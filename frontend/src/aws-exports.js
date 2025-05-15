/** aws-exports.js **/
const awsconfig = {
  Auth: {
    Cognito: {
      region: process.env.REACT_APP_COGNITO_REGION,
      userPoolId: process.env.REACT_APP_COGNITO_USER_POOL_ID,
      userPoolClientId: process.env.REACT_APP_COGNITO_APP_CLIENT_ID,
      loginWith: {
        oauth: {
          domain: process.env.REACT_APP_COGNITO_DOMAIN,
          scope: ['openid', 'email', 'profile'],
          redirectSignIn: [process.env.REACT_APP_REDIRECT_SIGN_IN],
          redirectSignOut: [process.env.REACT_APP_REDIRECT_SIGN_OUT],
          responseType: 'code',
        },
      },
    }
    },
    // API 엔드포인트 (EC2 컨테이너 URL)
    API: {
        endpoints: [
        {
            name: 'BackendAPI',
            endpoint: process.env.REACT_APP_API_URL,
        },
        ],
    },
};
export default awsconfig;