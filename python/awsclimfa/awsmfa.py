import argparse
import configparser
import json
import os
import string
import sys
from urllib.parse import _DefragResultBase
from os.path import expanduser

mfa=" "
awsConfig = configparser.ConfigParser()
awsCred   = configparser.ConfigParser()
home = expanduser("~")

def getconfig(profile):
    print("Searching the profile...")
    awsConfig.read("%s/.aws/config" % home)
    awsCred.read('%s/.aws/credentials' % home)
    
    # print(awsConfig)
    #search mfa profile in config
    try:
        mfa = str(awsConfig["profile " + profile]['mfa_serial'])
        print("Found exiting mfa arn...")
        print("Existing mfa arn: %s" % mfa)
        return 1
    except KeyError:
        profiles = set( awsCred.sections())
        configprofiles = set( awsConfig.sections())
        if( profile in profiles and "profile " + profile in configprofiles):
            print("Updating %s profile" % profile)
            return 1
        else:
            print("No such profile \"%s\" in config." % profile)
            newProfile = ""
            while newProfile  != 'y' and newProfile  != 'n':
                newProfile = str(input("would you like to create new profile y/n: "))
                newProfile  = newProfile.lower()
            if (newProfile == "y"):
                print(newProfile)
                try:
                    mfaARN = input("New mfa arn: ")
                    access = input("AWS ACCESS KEY: ")
                    key = input("AWS SECRET: ")
                    region = input("Default AWS Region: ")
                    output = input("Default Output style: ")
                except ValueError:
                    exit("Enter valid arn value")
                
                awsConfig.add_section("profile " + profile)
                awsCred.add_section(profile)
                awsConfig["profile " + profile]['mfa_serial'] = mfaARN
                #awsConfig["profile " + profile]['source_profile'] = profile
                awsConfig["profile " + profile]['region'] = region
                awsConfig["profile " + profile]['output'] = output
                awsCred[profile]['aws_access_key_id'] = access
                awsCred[profile]['aws_secret_access_key'] = key
                awsCred[profile]['aws_access_key_id_main']  = access
                awsCred[profile]['aws_secret_access_key_main']     = key
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

def configureMFA(profile="default"):
    print("Creating new mfa")
    if(getconfig(profile) == 1):
        try:
            mfaARN = str(input("New mfa arn: "))
            awsConfig["profile " + profile]['mfa_serial'] = mfaARN
            with open('%s/.aws/config' % home, 'w') as awsConfigfile:
                awsConfig.write(awsConfigfile)
        except ValueError:
            exit("Enter valid arn value")
    else:
        exit()
    
        

def renewMFA(profile="default"):
    if(getconfig(profile)):
        print("Renewing mfa...")
        
        awsCred[profile]['aws_access_key_id'] = awsCred[profile]['aws_access_key_id_main']
        awsCred[profile]['aws_secret_access_key'] = awsCred[profile]['aws_secret_access_key_main'] 

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
            exit("AWS was not happy with that one")
        
        # awsCred[profile]['aws_session_key_id_main']     = myjson['Credentials']['SessionToken']
        # awsCred[profile]['aws_session_access_key_main']     = myjson['Credentials']['SessionToken']
        awsCred[profile]['aws_access_key_id']     = myjson['Credentials']['AccessKeyId']
        awsCred[profile]['aws_secret_access_key'] = myjson['Credentials']['SecretAccessKey']
        awsCred[profile]['aws_session_token']     = myjson['Credentials']['SessionToken']
        

        with open('%s/.aws/credentials' % home, 'w') as awsCredfile:
            awsCred.write(awsCredfile)
        # os.environ['AWS_ACCESS_KEY_ID'] = myjson['Credentials']['AccessKeyId']
        # os.environ['AWS_SECRET_ACCESS_KEY'] = myjson['Credentials']['SecretAccessKey']
        # os.environ['AWS_SESSION_TOKEN'] = myjson['Credentials']['SessionToken']

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

