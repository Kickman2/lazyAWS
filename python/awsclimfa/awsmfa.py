import argparse
import configparser
import json
import os
import sys
from urllib.parse import _DefragResultBase
from os.path import expanduser

mfa=" "
awsConfig = configparser.ConfigParser()
awsCred   = configparser.ConfigParser()
home = expanduser("~")

def newConfig(profile):
    newProfile = ""
    while newProfile  != 'y' and newProfile  != 'n':
            newProfile = str(input("would you like to create new profile y/n: "))
            newProfile  = newProfile.lower()
        
    if (newProfile == "y"):
        configList= ('mfa_serial','region','output')
        credList = ('aws_access_key_id','aws_secret_access_key')
        awsConfig.add_section("profile " + profile)
        awsCred.add_section(profile)
        for item in configList:
            try:
                value = awsConfig["profile " + profile][item]
                print("Found exiting "+ item +" ...")
                print("Existing value: %s" % awsConfig["profile " + profile][item])
            except:
                try:
                    awsConfig["profile " + profile][item] = input("New "+ item +" : ")
                except ValueError:
                    exit("Enter valid arn value")
        

        for item in credList:
            try:
                value = awsConfig[profile][item]
                print("Found exiting "+ item +" ...")
                print("Existing value: %s" % awsCred[profile][item])
            except:
                try:
                    awsCred[profile][item] = input("New "+ item +" : ")
                except ValueError:
                    exit("Enter valid arn value")

        with open('%s/.aws/config' % home, 'w') as awsConfigfile:
            awsConfig.write(awsConfigfile)
        with open('%s/.aws/credentials' % home, 'w') as awsCredfile:
            awsCred.write(awsCredfile)
        return 0
    else:
        print("exit")
        exit()
    print("exit")
    exit()
    

def getConfig(profile):
    print("Searching the profile...")
    awsConfig.read("%s/.aws/config" % home)
    awsCred.read('%s/.aws/credentials' % home)
    
    # print(awsConfig)
    #search mfa profile in config
    profiles = set( awsCred.sections())
    configprofiles = set( awsConfig.sections())   
    
    if( profile in profiles and "profile " + profile in configprofiles):
        print("Found the %s profile" % profile)
        return 1
    else:       
        print("No such profile \"%s\" in config." % profile)
        return 0

    


def configureMFA(profile="default"):
     
    if ( getConfig(profile) == 1):
        print("Updating exiting profile")
    
    newConfig(profile)
    
        

def renewMFA( profile="default"):
    if( getConfig(profile) == 1):
        
        print("Renewing mfa...")
        
        try:
            mainkey = awsCred[profile]['aws_access_key_id_main']
            mainsecret = awsCred[profile]['aws_secret_access_key_main']
            awsCred[profile]['aws_access_key_id'] = awsCred[profile]['aws_access_key_id_main']
            awsCred[profile]['aws_secret_access_key'] = awsCred[profile]['aws_secret_access_key_main'] 
        except:
            awsCred[profile]['aws_access_key_id_main'] = awsCred[profile]['aws_access_key_id']
            awsCred[profile]['aws_secret_access_key_main'] = awsCred[profile]['aws_secret_access_key']
            with open('%s/.aws/credentials' % home, 'w') as awsCredfile:
                awsCred.write(awsCredfile)
               

        with open('%s/.aws/credentials' % home, 'w') as awsCredfile:
            awsCred.write(awsCredfile)
        try:
            OneTimeNumber = int(input("OTP from device: "))
        except ValueError:
            exit("OTP must be a number")
        response = os.popen("aws --output json --profile %s sts get-session-token --serial-number  %s --token-code %s" % (profile,
                                                                                                 awsConfig["profile " + profile]['mfa_serial'],
                                                                                    str(OneTimeNumber).zfill(6))).read()
        print(response)
        try:
            myjson = json.loads(response)
        except json.decoder.JSONDecodeError:
            exit("AWS was not happy with that one, if this you first time using check if AWS ACCESS key and SECRET key are corretly. \n Try Create new cofig with 'python awsmfa.py -n <profile>'.")

        
        # awsCred[profile]['aws_session_key_id_main']     = myjson['Credentials']['SessionToken']
        # awsCred[profile]['aws_session_access_key_main']     = myjson['Credentials']['SessionToken']
        awsCred[profile]['aws_access_key_id']     = myjson['Credentials']['AccessKeyId']
        awsCred[profile]['aws_secret_access_key'] = myjson['Credentials']['SecretAccessKey']
        awsCred[profile]['aws_session_token']     = myjson['Credentials']['SessionToken']
        with open('%s/.aws/credentials' % home, 'w') as awsCredfile:
                awsCred.write(awsCredfile)
        #os.environ['AWS_ACCESS_KEY_ID'] = myjson['Credentials']['AccessKeyId']
        #os.environ['AWS_SECRET_ACCESS_KEY'] = myjson['Credentials']['SecretAccessKey']
        #os.environ['AWS_SESSION_TOKEN'] = myjson['Credentials']['SessionToken']

def main():
  
    # Initialize parser
    parser = argparse.ArgumentParser()
    
    # Adding optional argument
    parser.add_argument("-n", "--configmfa", help ="Create/update mfa config")
    parser.add_argument("-r", "--renew", help = "Renew mfa access key")
    # Read arguments from command line
    args = parser.parse_args()
    if len(sys.argv)==1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    if args.configmfa:
        #create/update new mfa device
        configureMFA(args.configmfa)
    if args.renew:
        #renew mfa token
        renewMFA(args.renew)  
# Using the special variable 
# __name__
if __name__=="__main__":
    main()

