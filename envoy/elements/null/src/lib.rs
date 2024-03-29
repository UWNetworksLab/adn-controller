use proxy_wasm::traits::{Context, HttpContext};
use proxy_wasm::types::{Action, LogLevel};
use proxy_wasm::traits::RootContext;

// use prost::Message;
// TODO: Change if your change the proto file
pub mod ping {
    include!(concat!(env!("OUT_DIR"), "/ping_pb.rs"));
}

// TODO: Add global variable here

#[no_mangle]
pub fn _start() {
    proxy_wasm::set_log_level(LogLevel::Trace);
    proxy_wasm::set_root_context(|_| -> Box<dyn RootContext> { Box::new(NullRoot) });
    proxy_wasm::set_http_context(|context_id, _| -> Box<dyn HttpContext> {
        Box::new(NullBody { context_id })
    });
}

struct NullRoot;

impl Context for NullRoot {}

impl RootContext for NullRoot {
    fn on_vm_start(&mut self, _: usize) -> bool {
        log::warn!("executing on_vm_start");
        true
    }
}

struct NullBody {
    #[allow(unused)]
    context_id: u32,
}

impl Context for NullBody {}

impl HttpContext for NullBody {
    fn on_http_request_headers(&mut self, _num_of_headers: usize, end_of_stream: bool) -> Action {
        log::warn!("executing on_http_request_headers");
        if !end_of_stream {
            return Action::Continue;
        }

        Action::Continue
    }

    fn on_http_request_body(&mut self, _body_size: usize, end_of_stream: bool) -> Action {
        log::warn!("executing on_http_request_body");
        if !end_of_stream {
            return Action::Pause;
        }

        Action::Continue
    }

    fn on_http_response_headers(&mut self, _num_headers: usize, end_of_stream: bool) -> Action {
        log::warn!("executing on_http_response_headers");
        if !end_of_stream {
            return Action::Continue;
        }

        Action::Continue
    }

    fn on_http_response_body(&mut self, _body_size: usize, end_of_stream: bool) -> Action {
        log::warn!("executing on_http_response_body");
        if !end_of_stream {
            return Action::Pause;
        }

        Action::Continue
    }
}
