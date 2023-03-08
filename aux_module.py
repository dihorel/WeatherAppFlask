import string


class Password_verify:
    def __init__(self,password):
        self.password=password

    #check if password contains uppercase character
    def check_password_has_upper(self):
        for char in self.password:
            if char.isupper()==True:
                print('password has upper')
                return True
                break
        else:
            print('password has not upper')
            return False

    #check if password contains lowercase character       
    def check_password_has_lower(self):
        for char in self.password:
            if char.islower():
                print('password has lower')
                return True
                break
        else:
            print('password has not lower')
            return False

    #check if password contains special character
    def check_password_has_special(self):
        for char in self.password:
            if ord(char) in range(33,127) and not char.isalpha():
                print('password has special')
                return True
        else:
            print('password has not sepcial')
            return False

    #check password lenght
    def check_password_lenght(self):
        if len(self.password)>=8:
            print('password has more then 8')
            return True
        else:
            print('password has less then 8')
            return False



class Check_profile_data:
    def check_if_title(self,text):
        if text.istitle():
            return text
        else:
            return text.capitalize()

    def check_chars_in_name(self,text):
        alpha_letters_lower=string.ascii_letters
        allowed_chars=list(alpha_letters_lower)
        allowed_chars.append('-')
        allowed_chars.append(' ')
        for letter in text:
            if letter not in allowed_chars:
                return False
                break

        return True
        
    def extract_email_user(self,text):
        return text.split('@')[0]




