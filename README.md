# TikTokCreator
 Create TikToks from Viral Reddit Posts 
 # Needed .env fields: 
- REDDIT_CLIENT_ID=your_client_id
- REDDIT_CLIENT_SECRET=your_client_secret
- REDDIT_USERNAME=your_reddit_username
- REDDIT_PASSWORD=your_reddit_password
- AWS_ACCESS_KEY_ID=your_aws_key
- AWS_SECRET_ACCESS_KEY=your_aws_secret
- AWS_REGION=us-east-1
- AWS_POLLY_VOICE=Joanna


# Add mp4 or mp3 files to videos folder
Generate using yt-dlp for exampole: 
    yt-dlp -f "bestvideo[height=1080][fps=60]+bestaudio" --merge-output-format mp4 -o "C:\Users\comic\Downloads\subwaySurfer" https://www.youtube.com/watch?v=UCyKyyLzpD4

# Add lofi music mp4 or mp3 files to music folder