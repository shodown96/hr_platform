
class EmailService:
    # ... existing init ...
    
    async def send_otp_email(self, to_email: str, otp_code: str):
        """Send simple OTP email"""
        
        subject = "Password Reset Code"
        
        html_body = f"""
        <h2>Password Reset</h2>
        <p>Your verification code is:</p>
        <h1 style="color: #3498db; font-size: 32px;">{otp_code}</h1>
        <p>This code expires in 10 minutes.</p>
        <p>If you didn't request this, ignore this email.</p>
        """
        
        text_body = f"""
        Password Reset
        
        Your verification code is: {otp_code}
        
        This code expires in 10 minutes.
        """
        
        await self._send_email(to_email, subject, html_body, text_body)

