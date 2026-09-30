"""Explicit, synthetic-only Langfuse tracing with pre-export masking."""
import re
from .config import load_credentials

def scrub(value):
    if isinstance(value,str):
        value=re.sub(r'(?:sk|pk)-(?:lf-)?[A-Za-z0-9_-]{12,}','[REDACTED_KEY]',value)
        value=re.sub(r'[A-Za-z]:[\\/][^\s"\n]+','[REDACTED_PATH]',value)
        value=re.sub(r'/home/[^\s"\n]+','[REDACTED_PATH]',value)
        return value
    if isinstance(value,dict):
        return {k:('[REDACTED]' if any(t in k.lower() for t in ['secret','api_key','authorization','password']) else scrub(v)) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [scrub(v) for v in value]
    return value

def masked_batch(*,params):
    from langfuse.types import MaskOtelSpansResult,OtelSpanPatch
    patches={}
    for id,span in params.spans.items():
        changed={};deleted=[]
        for key,val in span.attributes.items():
            if key.startswith('exception.') or any(x in key.lower() for x in ['authorization','api_key','secret','file.path','user.id']):deleted.append(key)
            else:
                clean=scrub(val)
                if clean!=val:changed[key]=clean
        if changed or deleted:patches[id]=OtelSpanPatch(set_attributes=changed,delete_attributes=tuple(deleted))
    return MaskOtelSpansResult(span_patches=patches)

def client():
    load_credentials()
    from langfuse import Langfuse
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.resources import Resource
    provider=TracerProvider(resource=Resource({'service.name':'adoptlab','service.version':'0.1.0'}))
    return Langfuse(mask_otel_spans=masked_batch,mask=lambda *,data,**kw:scrub(data),
                    tracer_provider=provider,environment='adoptlab-synthetic',release='0.1.0',
                    should_export_span=lambda span:not any(e.name=='exception' for e in span.events))

class Recorder:
    def __init__(self,client):self.client=client
    def start_tool(self,name,args):
        return self.client.start_observation(name=name,as_type='tool',input=scrub(args))
    def start_generation(self,model,messages,tools):
        return self.client.start_observation(name='deepseek-tool-selection',as_type='generation',model=model,
                    model_parameters={'temperature':0,'thinking':'disabled','max_tokens':1024},input=scrub({'messages':messages,'tools':tools}))
    def end(self,span,output,usage=None):
        values={'output':scrub(output)}
        if usage:values['usage_details']={'input':usage['prompt_tokens'],'output':usage['completion_tokens']}
        span.update(**values);span.end()
