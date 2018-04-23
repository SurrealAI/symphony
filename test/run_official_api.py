from kubernetes import client, config
from pprint import pprint

# Configs can be set in Configuration class directly or using helper utility
config.load_kube_config()

v1 = client.CoreV1Api()
print("Listing pods with their IPs:")
# ret = v1.list_pod_for_all_namespaces(watch=False)
# for i in ret.items:
#     print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))


name = 'zliu-pixel-bench-16' # str | name of the Namespace
pretty = 'false' # str | If 'true', then the output is pretty printed. (optional)
exact = True # bool | Should the export be exact.  Exact export maintains cluster-specific fields like 'Namespace'. (optional)
export = True # bool | Should this value be exported.  Export strips fields that a user can not specify. (optional)

try:
    api_response = v1.read_namespace(name, pretty=pretty, exact=exact, export=export)
    print(api_response)
except Exception as e:
    print("Exception when calling CoreV1Api->read_namespace: %s\n" % e)