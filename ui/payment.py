import time
import stripe
import streamlit as st
from datetime import datetime
import os

class StripePaymentHandler:
    def __init__(self):
        stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]
        self.domain = st.secrets.get("DOMAIN", "http://localhost:8501")
        
    def create_checkout_session(self, amount: float, user_id: str, description: str):
        """Create a Stripe Checkout session"""
        success_url = f"{self.domain}/?payment=success&session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{self.domain}/?payment=cancel"
        
        return stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Product Generation',
                    },
                    'unit_amount': int(amount * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=user_id,
            metadata={
                "user_id": user_id,
                "service": "product_generation"
            }
        )

    def verify_payment(self, session_id: str):
        """Verify payment status"""
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == "paid":
                return {
                    "success": True,
                    "amount": session.amount_total / 100,
                    "customer_email": session.customer_details.email,
                    "metadata": session.metadata
                }
            return {"success": False}
        except Exception as e:
            st.error(f"Payment verification failed: {str(e)}")
            return {"success": False}

class PaymentUI:
    def __init__(self, auth_service):
        self.auth = auth_service
        self.payment_handler = StripePaymentHandler()
        self.PRODUCT_GENERATION_COST = 30.00

    def check_payment_required(self, user_id: str) -> bool:
        """Check if payment is required based on trial number"""
        status = self.auth.get_trial_status(user_id)
        # Payment required if no trials left AND no payment made
        return status["trial_remaining"] <= 0 


    def show_payment_required(self, action_name: str):
        """Show payment required message with trial info"""
        user_id = st.session_state.current_user["_id"]
        status = self.auth.get_trial_status(user_id)
        
        if status["trial_remaining"] > 0:
            # User has free trials remaining
            if st.button(f"Use Free Trial (Remaining: {status['trial_remaining']})"):
                self.auth.decrement_trial(user_id)
                return False  # Don't show payment, use trial
            return True  # Still show payment option
            
        # No trials left
        st.error(f"🚨 You've used all your free trials. Please pay ${self.PRODUCT_GENERATION_COST} to {action_name}.")
        
        if st.button(f"💳 Pay ${self.PRODUCT_GENERATION_COST}"):
            st.session_state.payment_page = True
            st.rerun()
        
        return True  # Payment required

    def _handle_payment_return(self, query_params):
        """Handle return from Stripe checkout"""
        if query_params["payment"][0] == "success":
            session_id = query_params.get("session_id", [None])[0]
            if session_id:
                return self._verify_payment(session_id)
            else:
                st.error("Payment verification failed - missing session ID")
        else:
            st.warning("Payment was canceled. You can try again.")
        return False

    def _verify_payment(self, session_id):
        """Verify and process successful payment"""
        with st.spinner("Verifying payment..."):
            result = self.payment_handler.verify_payment(session_id)
            
            if result["success"]:
                # Record transaction
                transaction = {
                    "transaction_id": session_id,
                    "amount": result["amount"],
                    "currency": "usd",
                    "description": "Product Generation",
                    "status": "succeeded",
                    "date": datetime.now().isoformat(),
                    "service": "product_generation"
                }
                
                # Update user record
                user_id = result["metadata"].get("user_id")
                if user_id:
                    self.auth.update_user_payment(user_id, transaction)
                    
                    st.success("Payment verified successfully! You can now generate products.")
                    st.balloons()
                    time.sleep(2)
                    st.experimental_set_query_params()
                    st.session_state.payment_verified = True
                    return True
                else:
                    st.error("User not found in payment metadata")
            else:
                st.error("Payment verification failed. Please contact support.")
        return False