# 1. Clone repo
git clone https://github.com/solgar/solgar-internal-platform.git
cd solgar-internal-platform

# 2. Virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Requirements
pip install -r requirements.txt

# 4. Create .env file
cp .env.example .env

# 5. DB
python manage.py migrate

# 6. Run
python manage.py runserver
