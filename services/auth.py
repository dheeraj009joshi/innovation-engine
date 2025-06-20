


import secrets
import streamlit as st
from datetime import datetime
import hashlib
import uuid
from db.mongo import get_db


class AuthService:
    def __init__(self):
        self.db = get_db()
        self.users = self.db["users"]
        self.projects = self.db["projects"]
        self.results = self.db["agent_results"]

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def create_user(self, username, email, password):
        if self.users.find_one({"$or": [{"username": username}, {"email": email}]}):
            return False
        self.users.insert_one({
            "_id": str(uuid.uuid4()),
            "username": username,
            "email": email,
            "password": self.hash_password(password),
            "created_at": datetime.now(),
            "last_login": None,
            "current_project": None
        })
        return True
    

    def verify_user(self, username, password):
        user = self.users.find_one({"username": username})
        if user and user["password"] == self.hash_password(password):
            self.users.update_one(
                {"_id": user["_id"]},
                {"$set": {"last_login": datetime.now()}}
            )
            return user
        return None

    def save_agent_results(self, project_id, results):
        try:
            self.results.update_one(
                {"project_id": project_id},
                {"$set": {
                    "results": results,
                    "updated_at": datetime.now()
                }},
                upsert=True
            )
            self.projects.update_one(
                {"_id": project_id},
                {"$set": {
                    "wizard_step": 3,
                    "completed_steps": [1, 2, 3],
                    "updated_at": datetime.now()
                }}
            )
            return True
        except Exception as e:
            st.error(f"Error saving results: {str(e)}")
            return False

    def save_product_results(self, project_id, product_ideas):
        try:
            existing = self.results.find_one({"project_id": project_id})
            new_generation = {
                "_id": str(uuid.uuid4()),
                "created_at": datetime.now(),
                "ideas": product_ideas
            }

            if existing and "results" in existing:
                results_data = existing["results"]

                if isinstance(results_data.get("ProductGenerationAgent"), dict):
                    generations = results_data["ProductGenerationAgent"].get("generations", [])
                    generations.append(new_generation)

                    update_data = {
                        "$set": {
                            "results.ProductGenerationAgent.generations": generations,
                            "results.ProductGenerationAgent.latest": new_generation,
                            "updated_at": datetime.now()
                        }
                    }

                elif isinstance(results_data.get("ProductGenerationAgent"), list):
                    old_ideas = results_data["ProductGenerationAgent"]

                    update_data = {
                        "$set": {
                            "results.ProductGenerationAgent": {
                                "generations": [
                                    {
                                        "_id": str(uuid.uuid4()),
                                        "created_at": datetime.now(),
                                        "ideas": old_ideas
                                    },
                                    new_generation
                                ],
                                "latest": new_generation
                            },
                            "updated_at": datetime.now()
                        }
                    }

                else:
                    update_data = {
                        "$set": {
                            "results.ProductGenerationAgent": {
                                "generations": [new_generation],
                                "latest": new_generation
                            },
                            "updated_at": datetime.now()
                        }
                    }
            else:
                update_data = {
                    "$set": {
                        "results.ProductGenerationAgent": {
                            "generations": [new_generation],
                            "latest": new_generation
                        },
                        "updated_at": datetime.now()
                    }
                }

            self.results.update_one(
                {"project_id": project_id},
                update_data,
                upsert=True
            )
            self.projects.update_one(
                {"_id": project_id},
                {"$set": {
                    "wizard_step": 4,
                    "completed_steps": [1, 2, 3, 4],
                    "updated_at": datetime.now()
                }}
            )
            return True
        except Exception as e:
            st.error(f"Error saving product ideas: {str(e)}")
            return False

    def save_file_metadata(self, project_id, file_metadata):
        try:
            self.projects.update_one(
                {"_id": project_id},
                {"$set": {
                    "file_metadata": file_metadata,
                    "updated_at": datetime.now()
                }}
            )
            return True
        except Exception as e:
            st.error(f"Error saving file metadata: {str(e)}")
            return False

    def get_file_metadata(self, project_id):
        try:
            project = self.projects.find_one({"_id": project_id})
            return project.get("file_metadata", {})
        except Exception as e:
            st.error(f"Error retrieving file metadata: {str(e)}")
            return {}

    def save_file_metadata(self, project_id, file_metadata):
        """Save file metadata to project"""
        return self.projects.update_one(
            {"_id": project_id},
            {"$set": {"file_metadata": file_metadata}},
            upsert=True
        )
    
    def update_project(self, project_id, update_dict):
        """Update project with arbitrary fields"""
        return self.projects.update_one(
            {"_id": project_id},
            {"$set": update_dict}
        )
    
    def delete_project(self,project_id):
        return self.projects.delete_one({"_id":project_id})
    

    
    def reset_password(self, token, new_password):
        user = self.users.find_one({"reset_token": token})
        if not user:
            return False
        self.users.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "password": self.hash_password(new_password),
                "reset_token": None
            }}
        )
        return True

    def create_reset_token(self, email):
        user = self.users.find_one({"email": email})
        if not user:
            return None
        token = secrets.token_urlsafe(32)
        self.users.update_one(
            {"email": email},
            {"$set": {"reset_token": token, "reset_token_expiry": datetime.now()}}
        )
        return token

        # In your AuthService class, add these methods:
    def get_trial_status(self, user_id: str) -> dict:
        """Get user's trial status"""
        user = self.users.find_one(
            {"_id": user_id},
            {"payment_info": 1, "usage_stats": 1}
        )
        if not user:
            return {"trial_remaining": 0, "has_paid": False}
        
        return {
            "trial_remaining": user.get("payment_info", {}).get("trial_number", 1),
            "has_paid": user.get("payment_info", {}).get("has_paid", False)
        }

    def decrement_trial(self, user_id: str) -> bool:
        """Decrement trial count when user uses a free attempt"""
        result = self.users.update_one(
            {"_id": user_id},
            {"$inc": {"payment_info.trial_number": -1}}
        )
        return result.modified_count > 0

        # Add to your AuthService class
    def update_user_payment(self, user_id: str, transaction_data: dict) -> bool:
        """Record a successful payment transaction"""
        return self.users.update_one(
            {"_id": user_id},
            {
                "$set": {
                    "payment_info.has_paid": True,
                    "payment_info.last_payment_date": datetime.now()
                },
                "$push": {"transactions": transaction_data},
                "$inc": {"usage_stats.products_generated": 1}
            }
        ).modified_count > 0

    def get_user_payment_status(self, user_id: str) -> dict:
        """Get user's payment status"""
        user = self.users.find_one(
            {"_id": user_id},
            {"payment_info": 1, "transactions": 1, "usage_stats": 1}
        )
        if not user:
            return {}
        
        return {
            "has_paid": user.get("payment_info", {}).get("has_paid", False),
            "trial_available": not user.get("payment_info", {}).get("trial_used", False),
            "last_transaction": user.get("transactions", [])[-1] if user.get("transactions") else None
        }