import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
import joblib
import os

# Dummy data (you can replace this with your own dataset)
data = {
    'description': ['Grocery shopping', 'Uber ride', 'Electricity bill', 'Restaurant dinner', 'Internet bill'],
    'category': ['Food', 'Transport', 'Utilities', 'Food', 'Utilities']
}

df = pd.DataFrame(data)

# Create model
model = make_pipeline(CountVectorizer(), MultinomialNB())
model.fit(df['description'], df['category'])

# Save model to tracker folder
output_path = os.path.join('tracker', 'expense_classifier.pkl')
joblib.dump(model, output_path)

print(f"✅ Model saved at: {output_path}")
