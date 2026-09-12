import inspect
from collections.abc import Callable
from typing import Any, TypeVar, get_type_hints

from fastapi import APIRouter, Depends, params
from fastapi.routing import APIRoute

T = TypeVar("T")


def cbv(router: APIRouter) -> Callable[[type[T]], type[T]]:
    """Transforma uma classe em class-based view: atributos anotados com `Depends(...)`
    são injetados uma vez por request; métodos decorados com `@router.<verbo>(...)`
    viram `self.metodo(...)`."""

    def decorator(cls: type[T]) -> type[T]:
        _build_init(cls)
        _rebind_routes(cls, router)
        return cls

    return decorator


def _build_init(cls: type) -> None:
    if "__init__" in cls.__dict__:
        return

    hints = get_type_hints(cls)
    dependencies = [
        (name, hints[name], value)
        for name, value in vars(cls).items()
        if name in hints and isinstance(value, params.Depends)
    ]

    def __init__(self: Any, **kwargs: Any) -> None:
        for name, _, _ in dependencies:
            setattr(self, name, kwargs[name])

    signature = inspect.Signature(
        [
            inspect.Parameter(
                name,
                kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=default,
                annotation=hint,
            )
            for name, hint, default in dependencies
        ]
    )
    __init__.__signature__ = signature
    cls.__init__ = __init__
    # inspect.signature(cls) lê __signature__ da classe, não do __init__ (necessário
    # pro FastAPI resolver Depends(cls) com os parâmetros certos)
    cls.__signature__ = signature


def _rebind_routes(cls: type, router: APIRouter) -> None:
    cls_methods = {func for _, func in inspect.getmembers(cls, inspect.isfunction)}
    cbv_routes = [
        route
        for route in router.routes
        if isinstance(route, APIRoute) and route.endpoint in cls_methods
    ]
    if not cbv_routes:
        return

    pending_router = APIRouter()
    for route in cbv_routes:
        router.routes.remove(route)
        _fix_endpoint_signature(cls, route.endpoint)
        route.dependencies = [d for d in route.dependencies if d not in router.dependencies]
        pending_router.routes.append(route)

    router.include_router(pending_router)


def _fix_endpoint_signature(cls: type, endpoint: Callable) -> None:
    old_signature = inspect.signature(endpoint)
    old_parameters = list(old_signature.parameters.values())
    if not old_parameters or old_parameters[0].name != "self":
        raise TypeError(
            f"'{endpoint.__qualname__}' precisa ter 'self' como primeiro parâmetro para usar @cbv"
        )

    self_parameter = old_parameters[0].replace(default=Depends(cls))
    new_parameters = [self_parameter] + [
        parameter.replace(kind=inspect.Parameter.KEYWORD_ONLY) for parameter in old_parameters[1:]
    ]
    endpoint.__signature__ = old_signature.replace(parameters=new_parameters)
