# db_migration.py
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

load_dotenv()

def migrate_database():
    try:
        client = MongoClient(os.getenv("MONGO_URI"))
        db = client["innovation_engine"]
        results_collection = db["agent_results"]
        
        # Find all documents with old-style product generation data
        old_style_docs = results_collection.find({
            "results.ProductGenerationAgent": {"$type": "array"}
        })
        
        migration_count = 0
        
        for doc in old_style_docs:
            project_id = doc["project_id"]
            old_ideas = doc["results"]["ProductGenerationAgent"]
            
            # Skip if already migrated
            if not isinstance(old_ideas, list):
                continue
            
            # Create new structure
            new_gen = {
                "id": ObjectId(),
                "created_at": datetime.now(),
                "ideas": old_ideas
            }
            
            new_structure = {
                "generations": [new_gen],
                "latest": new_gen
            }
            
            # Update document
            results_collection.update_one(
                {"_id": doc["_id"]},
                {"$set": {
                    "results.ProductGenerationAgent": new_structure,
                    "updated_at": datetime.now()
                }}
            )
            
            migration_count += 1
            print(f"Migrated project: {project_id}")
        
        print(f"Migration complete. Updated {migration_count} records.")
        
    except Exception as e:
        print(f"Migration failed: {str(e)}")

if __name__ == "__main__":
    migrate_database()