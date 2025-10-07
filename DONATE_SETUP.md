# Buy Me a Coffee Setup Guide

## Overview
A "Buy Me a Coffee" donation button has been added to the Indieflix header to allow users to support the project.

## Setup Instructions

### 1. Create a Buy Me a Coffee Account
1. Go to [buymeacoffee.com](https://www.buymeacoffee.com/)
2. Sign up for a free account
3. Choose your username (e.g., `indieflix` or `your-name`)
4. Set up your profile

### 2. Update the Link in Your Code

Open `frontend/index.html` and find this line (around line 28):

```html
<a href="https://www.buymeacoffee.com/YOUR_USERNAME" 
```

Replace `YOUR_USERNAME` with your actual Buy Me a Coffee username:

```html
<a href="https://www.buymeacoffee.com/indieflix" 
```

### 3. Test the Button

1. Save the file
2. Refresh your website
3. Click the "Buy me a coffee" button in the header
4. Verify it takes you to your Buy Me a Coffee page

## Button Features

- **Desktop**: Shows coffee icon + "Buy me a coffee" text
- **Mobile**: Shows only the coffee icon to save space
- **Styling**: Glass morphism effect with purple gradient header
- **Hover effect**: Subtle lift animation on hover

## Customization Options

### Change Button Text

In `frontend/index.html`, find:
```html
<span>Buy me a coffee</span>
```

Change to whatever you prefer:
```html
<span>Support this project</span>
```

### Change Button Color

In `frontend/styles.css`, find `.coffee-btn` and modify:
```css
.coffee-btn {
    background: rgba(255, 255, 255, 0.2);  /* Change transparency */
    border: 2px solid rgba(255, 255, 255, 0.3);  /* Change border */
}
```

### Remove Button Completely

If you don't want the donation button:
1. Open `frontend/index.html`
2. Delete the entire `<div class="header-actions">...</div>` section
3. The header will automatically center the title

## Alternative Donation Platforms

You can use other platforms by simply changing the URL:
- **Ko-fi**: `https://ko-fi.com/YOUR_USERNAME`
- **Patreon**: `https://www.patreon.com/YOUR_USERNAME`
- **GitHub Sponsors**: `https://github.com/sponsors/YOUR_USERNAME`

Just update the `href` attribute in the HTML file.

## Questions?

If you have issues with the button, check:
1. Did you replace `YOUR_USERNAME`?
2. Is your Buy Me a Coffee page public?
3. Did you clear your browser cache?
