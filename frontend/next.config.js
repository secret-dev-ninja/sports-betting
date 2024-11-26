const dotenv = require('dotenv')
const path = require('path')

dotenv.config({
  path: path.resolve(__dirname, '../.env')
});

module.exports = {
  typescript: {
    ignoreBuildErrors: true
  },
  env: {
    REACT_APP_WS_URL: process.env.REACT_APP_WS_URL,
    REACT_APP_API_URL: process.env.REACT_APP_API_URL,
    REACT_APP_CHART_API_URL: process.env.REACT_APP_CHART_API_URL
  }
}