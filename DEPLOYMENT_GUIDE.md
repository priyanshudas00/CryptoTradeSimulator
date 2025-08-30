# Crypto Trade Simulator - Netlify Deployment Guide

## Overview
This guide will help you deploy the Crypto Trade Simulator frontend to Netlify. The frontend is a static website that works both with and without the backend WebSocket server.

## Prerequisites
- A Netlify account (free tier is sufficient)
- Git repository of your project (GitHub, GitLab, or Bitbucket)
- Node.js installed locally (for testing)

## Deployment Methods

### Method 1: Git-based Deployment (Recommended)

1. **Push your code to a Git repository**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin <your-repository-url>
   git push -u origin main
   ```

2. **Connect to Netlify**
   - Go to [netlify.com](https://netlify.com) and sign in
   - Click "Add new site" → "Import an existing project"
   - Connect your Git provider (GitHub, GitLab, etc.)
   - Select your repository

3. **Configure Build Settings**
   - Build command: `echo 'No build command needed for static site'`
   - Publish directory: `.` (root directory of the frontend folder)
   - Click "Deploy site"

### Method 2: Manual Drag & Drop Deployment

1. **Prepare your files**
   - Ensure all frontend files are in the `frontend` directory
   - The directory should contain:
     - `index.html`
     - `styles.css` 
     - `app.js`
     - `netlify.toml`
     - `package.json` (optional for local development)

2. **Deploy to Netlify**
   - Go to [netlify.com](https://netlify.com)
   - Drag and drop the entire `frontend` folder to the deployment area
   - Netlify will automatically deploy your site

### Method 3: Netlify CLI Deployment

1. **Install Netlify CLI**
   ```bash
   npm install -g netlify-cli
   ```

2. **Login to Netlify**
   ```bash
   netlify login
   ```

3. **Initialize and deploy**
   ```bash
   cd frontend
   netlify init
   netlify deploy --prod
   ```

## Configuration Details

### Netlify.toml Settings
The existing `netlify.toml` file includes:
- **Publish directory**: Root folder (`.`)
- **Build command**: Echo statement (no build needed)
- **Redirects**: SPA-style routing (all routes to index.html)
- **Headers**: Security headers and caching policies
- **Node version**: Node.js 18 for any build processes

### Environment Variables (Optional)
If you deploy the backend separately, you can set environment variables in Netlify:
- `REACT_APP_WS_URL`: WebSocket URL for your deployed backend
- Set these in Netlify dashboard → Site settings → Environment variables

## Testing the Deployment

### Local Testing
```bash
cd frontend
npm install
npm start
# Open http://localhost:3000
```

### After Deployment
1. Visit your Netlify URL (e.g., `https://your-site-name.netlify.app`)
2. Test the simulation functionality
3. Verify that charts load correctly
4. Check that dark/light mode toggle works

## Backend Deployment (Optional)

The frontend works with simulated data by default. If you want to use the real WebSocket backend:

1. **Deploy the Python proxy server** to a service like:
   - Heroku
   - Railway
   - AWS Elastic Beanstalk
   - DigitalOcean App Platform

2. **Update the WebSocket URL** in `frontend/app.js`:
   ```javascript
   // Change from:
   const wsUrl = "ws://localhost:8765";
   
   // To your deployed backend URL:
   const wsUrl = "wss://your-backend-url.com";
   ```

## Troubleshooting

### Common Issues

1. **404 errors on page refresh**
   - Fixed by the SPA redirects in `netlify.toml`

2. **Charts not loading**
   - Check that Chart.js CDN is accessible
   - Verify internet connection

3. **WebSocket connection errors**
   - Frontend uses simulated data as fallback
   - Check browser console for specific errors

4. **Build failures**
   - Ensure `netlify.toml` is in the root of deployed directory
   - Verify Node.js version compatibility

### Netlify Dashboard Features

- **Deploy previews**: Automatic previews for pull requests
- **Form handling**: Built-in form submission handling
- **Analytics**: Basic analytics available
- **Domain management**: Custom domains and HTTPS

## Performance Optimization

The site is already optimized with:
- CDN delivery via Netlify's global network
- Proper caching headers for static assets
- Compressed assets delivery
- Security headers for protection

## Support

For issues with Netlify deployment:
- Check Netlify documentation: https://docs.netlify.com/
- View deployment logs in Netlify dashboard
- Check browser console for frontend errors

For application-specific issues:
- Review the browser console for JavaScript errors
- Test locally first to isolate deployment vs code issues
