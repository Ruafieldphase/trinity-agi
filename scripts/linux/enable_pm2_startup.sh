#!/bin/bash
# Enable PM2 startup
sudo env PATH=$PATH:/usr/bin /usr/local/lib/node_modules/pm2/bin/pm2 startup systemd -u bino --hp /home/bino

# Save current process list
pm2 save

echo "✅ PM2 Persistence Enabled!"
