#!/usr/bin/env python3
"""
Example of how to call DMAP deployment from another service
"""

from deploy import deploy_dmap_application

def main():
    """Example function showing how your service would call the deployment"""
    
    # This is the format your service will use
    vm_config = {
        "vm1": ["54.209.105.96", "ubuntu", "postgres"],
        "vm2": ["54.205.202.78", "ubuntu", "neo4j"],
        "vm3": ["52.90.125.49", "ubuntu", "kafka"],
        "vm4": ["3.93.70.249", "ubuntu", "backend"]
    }
 
    
    print("Starting DMAP deployment from service...")
    
    # Call the deployment function
    result = deploy_dmap_application(vm_config)
    
    if result:
        print("Deployment successful!")
        return True
    else:
        print("Deployment failed!")
        return False

if __name__ == "__main__":
    main()