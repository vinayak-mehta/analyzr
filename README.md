analyzr
======
Real-time twitter analytics on your terminal!

## Demo
![Demo](https://raw.githubusercontent.com/vinayak-mehta/analyzr/master/demo.gif)

## Dependencies
analyzr is tested to work with Python 3.5.1.
Dependencies include tweepy and redis-py.

## Setup and Usage
1. You'll need to create an app on Twitter to use their API. Just go to [https://apps.twitter.com/](https://apps.twitter.com/app/new) and click on **Create New App**. After you generate the keys, replace `x-x-x-x`s in `analyzr.py` with them.

2. You'll need to install redis on your box. 
On *Arch Linux*, you can do this with `pacman -S redis`. 
Make sure you start the redis server. You can do this with `systemd` by 
	<pre>
	systemctl enable redis.service
	systemctl start redis.service
	</pre>

3. Install the dependencies with `pip install -r requirements.txt`.

4. Run `python analyzr.py`.

5. Profit.